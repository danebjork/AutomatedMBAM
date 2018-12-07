from sympy.printing import julia_code
from sympy import sympify
from .basediff import BaseDiffParser
import logging

class DAEParser(BaseDiffParser):
    """Used for parsing ODE models.
    """
    # CAST PARAMS AS PARAMS for julia_swap
    def __init__(self, mbam_model, data_path):
        """
        Parameters
        ----------
        mbam_model : ``mbammodel``
            Can be any of the following: Function, ODE, DAE.
        data_path : ``str``
            The full path to the hdf5 file to be included in the
            model.
        """
        super().__init__(mbam_model, data_path)
        self.add_derivs_to_julia_swap()
        self.create_icd_swap()
        self.logger = logging.getLogger("MBAM.DAEParser")
        self.logger.debug("Initializing DAEParser")

    def add_derivs_to_julia_swap(self):
        """ Adding derivatives to the substitution list of julia vars for
        every variable in the model.

        Example
        -------
        x_1 => x_1dot => _dx[1]
        """
        for i, v in enumerate(self.mm.model_vs.list):
            self.julia_swap.append((v + "dot", '_dx[{0}]'.format(i+1)))

    def write_script(self):
        self.script = self.write_imports()
        self.script += self.write_params()
        self.script += self.write_inputs()

        ## ODE Specific
        self.script += self.write_ic()
        self.script += self.write_res()

        self.script += self.write_obs()
        self.script += self.write_data()
        self.script += self.write_dvars()
        self.script += self.write_model()

        self.script += self.write_constants()
        self.script += self.write_param_transforms()
        self.script += 'model = Models.Model(parametricmodel)\n'
        if self.options['bare']:
            self.script += '\n\n'
            self.script += self.write_bare_model()
        self.script += 'xi = ParametricModels.xvalues(parametricmodel)\n'
        self.script += 'end # module'
        self.script = self.find_replace_vectorized(self.script)

    def write_bare_model(self):
        ret = ''
        ret += 'zerodata = ParametricModels.OLSData("%s"_zero, zero(ydata))\n' % self.name
        ret += 'bareparametricmodel = @ParametricModels.DAEModel(zerodata, %s, ic, res, obs, _t, (), Tuple{Symbol, Any}[])\n' % self.name
        ret += self.write_param_transforms(bare=True)
        ret += 'modelbare = Models.Model(bareparametricmodel)\n'
        return ret

    def create_icd_swap(self):
        """Substitute the variables in the ICD's with their corresponding
        initial condition.

        Example
        -------
        if IC: [x_1_init + p1], then ICD[x_1] => ICD[ps.x_1_init + ps.p1]
        """
        self.icd_swap = []
        for i, v in enumerate(self.mm.model_vs.list):
            # new_v = "ps." + v + "_init"
            new_v = self.mm.model_eqs['ic'].eqs.sym_list[i]['eq']
            self.icd_swap.append((sympify(v), new_v))

    def write_ic_subs(self):
        all_subs = ""
        for i, eq in enumerate(self.mm.model_eqs['ic'].sbs.dict['sbs']):
            eq = str(eq['sym']) + " = " + julia_code(sympify(eq['eq']).subs(self.icd_swap).subs(self.julia_swap))
            all_subs += (eq + "\n")

        for i, eq in enumerate(self.mm.model_eqs['res'].sbs.dict['sbs']):
            eq = str(eq['sym']) + " = " + julia_code(sympify(eq['eq']).subs(self.icd_swap).subs(self.julia_swap))
            all_subs += ("\t" + eq + "\n")

        return all_subs

    def write_ic(self):
        """Specialty function for writing the IC function.
        """
        ret = 'function ic(ps::%s{T}) where T <: Real\n' % self.name
        ret += self.write_ic_subs()
        ret += self.write_substitutions(self.mm.model_eqs['ic'].sbs_sym_list)
        ret += '\treturn '
        ret += self.write_equation_list(self.mm.model_eqs['ic'].eqs_sym_list)
        ret += ", "
        ret += self.write_icd_list(self.mm.model_eqs['icd'].eqs_sym_list)
        ret += '\nend\n\n'
        return ret

    def write_icd_list(self, eq_list):
        """Specialty funciton for writing ICD's in a list format.
        """
        ret = 'T['
        for i, eq in enumerate(eq_list):
            ret += julia_code(eq['eq'].subs(self.icd_swap).subs(self.julia_swap))
            if i != len(eq_list)-1:
                ret += ', '
        ret += ']'
        return ret

    def write_res(self):
        """Specialty funciton for writing RES function.
        """
        ret = 'function res(ps::%s{T}, _t, _x, _dx, err) where T <: Real\n' % self.name
        ret += self.write_substitutions(self.mm.model_eqs['res'].sbs_sym_list)
        ret += "\t_inp = inp(ps, _t)\n"
        ret += self.write_res_equations()
        return ret

    def write_res_equations(self):
        """Specialty funciton for writing RES equations.
        """
        ret = ''
        for i, eq in enumerate(self.mm.model_eqs['res'].eqs_sym_list):
            ret += '\t'
            ret += 'err[{0}] = '.format(i+1)
            ret += julia_code(eq['eq'].subs(self.julia_swap))
            ret += '\n'
        ret += '\tnothing\n'
        ret += 'end\n\n'
        return ret

    def write_dvars(self):
        """Returnes a list of true/false for each variable, where true = dynamic
        false = algebraic.
        """
        ret = "differential_vars = ["
        for v in self.mm.model_vs.dict['vs']:
            if v['type'] == "dynamic":
                ret += "true, "
            else:
                ret += "false, "
        ret = ret[:-2] + "]\n"
        return ret

    def write_model(self):
        return 'parametricmodel = @ParametricModels.DAEModel(data, %s, ic, res, obs, _t, differential_vars, %s, %s)\n' %(self.name, self.parse_args(), self.parse_kwargs())
