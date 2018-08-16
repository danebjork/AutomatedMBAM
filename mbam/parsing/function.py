from sympy.printing import julia_code
from .basediff import BaseDiffParser

class FunctionParser(BaseDiffParser):
    """Used for parsing models composed of simple algebraic functions.
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
        self.logger = logging.getLogger("MBAM.FunctionParser")
        self.logger.debug("Initializing FunctionParser")

    def write_script(self):
        self.script = self.write_imports()
        self.script += self.write_params()
        self.script += self.write_inputs()

        self.script += self.write_f()

        self.script += self.write_data()
        self.script += self.write_model()
        self.script += self.write_constants()
        self.script += self.write_param_transforms()
        self.script += 'model = Models.Model(parametricmodel)\n'
        if self.options['bare']:
            self.script += '\n\n'
            self.script += self.write_bare_model()
        self.script += 'xi = ParametricModels.xvalues(parametricmodel)\n'
        self.script += 'end # module'

    def write_f(self):
        ret = 'function f(ps::%s{T}, t) where T <: Real\n' % self.name
        ret += "\t_inp = inp(ps, t)\n"
        ret += self.write_substitutions(self.mm.model_eqs['f'].sbs_sym_list)
        ### WRITE OWN EQUATION FUNCTION ###
        ret += self.write_equation_return(self.mm.model_eqs['f'].eqs_sym_list)
        return ret

    def write_bare_model(self):
        ret = ''
        ret += 'zerodata = ParametricModels.OLSData("%s"_zero, zero(ydata))\n' % self.name
        ret += 'bareparametricmodel = @ParametricModels.ParametricModel(zerodata, %s, ic, f, (_t,), Tuple{Symbol, Any}[])\n' % self.name
        ret += self.write_param_transforms(bare=True)
        ret += 'modelbare = Models.Model(bareparametricmodel)\n'
        return ret

    def write_model(self):
        return 'parametricmodel = @ParametricModels.ParametricModel(data, %s, f, (_t,), Tuple{Symbol, Any}[])\n' % self.name
