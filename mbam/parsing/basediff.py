from .base import BaseParser

class BaseDiffParser(BaseParser):
    """Parent class for all **differential** model parsers.

    Adds observation parsing to the BaseParser class.
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

    def write_obs(self):
        ret = 'function obs(ps::%s{T}, _t, _x) where T <: Real\n' % self.name
        ret += self.write_substitutions(self.mm.model_eqs['obs'].sbs_sym_list)
        ret += self.write_equation_return(self.mm.model_eqs['obs'].eqs_sym_list)
        return ret
