from sympy.printing import julia_code
from .basediff import BaseDiffParser
import logging

class ODEParser(BaseDiffParser):
    """Used for parsing ODE models.
    """
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
        self.logger = logging.getLogger("MBAM.ODEParser")
        self.logger.debug("Initializing ODEParser")

    def write_script(self):
        self.script = self.write_imports()
        self.script += self.write_params()
        self.script += self.write_inputs()

        ## ODE Specific
        self.script += self.write_ic()
        self.script += self.write_rhs()
        ## Base
        self.script += self.write_obs()
        self.script += self.write_data()
        ## ODE Specific
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
        ret += 'bareparametricmodel = @ParametricModels.ODEModel(zerodata, %s, ic, rhs, obs, _t, (), Tuple{Symbol, Any}[])\n' % self.name
        ret += self.write_param_transforms(bare=True)
        ret += 'modelbare = Models.Model(bareparametricmodel)\n'
        return ret

    def write_ic(self):
        ret = 'function ic(ps::%s{T}) where T <: Real\n' % self.name
        ret += self.write_substitutions(self.mm.model_eqs['ic'].sbs_sym_list)
        ret += self.write_equation_return(self.mm.model_eqs['ic'].eqs_sym_list)
        return ret

    def write_rhs(self):
        ret = 'function rhs(ps::%s{T}, _t, _x, _dx) where T <: Real\n' % self.name
        ret += self.write_substitutions(self.mm.model_eqs['rhs'].sbs_sym_list)
        ret += "\t_inp = inp(ps, _t)\n"
        ret += self.write_rhs_equations()
        return ret

    def write_rhs_equations(self):
        """RHS function follow a different formatting for parsing equations.
        This is their specialized parsing function.
        """
        ret = ''
        for i, eq in enumerate(self.mm.model_eqs['rhs'].eqs_sym_list):
            ret += '\t'
            ret += '_dx[{0}] = '.format(i+1)
            ret += julia_code(eq['eq'].subs(self.julia_swap))
            ret += '\n'
        ret += '\tnothing\n'
        ret += 'end\n\n'
        return ret

    def write_model(self):
        return 'parametricmodel = @ParametricModels.ODEModel(data, %s, ic, rhs, obs, _t, %s, %s)\n' %(self.name, self.parse_args(), self.parse_kwargs())
