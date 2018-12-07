import os
from sympy.printing import julia_code
from sympy import Symbol
import json
import logging
import re

class BaseParser:
    """Parent class for all model parsers.
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
        self.logger = logging.getLogger("MBAM.BaseParser")
        self.logger.debug("Initializing BaseParser")
        self.mm = mbam_model
        self.create_default_options()
        # self.data_path = data_path
        self.data_path = 'temp.h5' # os.path.join(os.pardir, 'temp.h5') # data should be in parent directory
        self.script = '\n'
        self.dir = os.path.join("julia_scripts", "models")
        self.name = self.mm.name
        self.file_name = self.name + ".jl"
        self.file_path = os.path.join(os.getcwd(), os.path.join(self.dir, self.file_name))
        self.create_julia_swap()

    def update_options(self, options):
        """Creates and saves a new script generated with the given options.

        Parameters
        ----------
        options : ``dict``
            Must follow format: {"bare": ``bool``, "weights": ``bool``, "imports": ``string``, "args": ``string``, "kwargs": ``string``}
        """
        self.logger.debug("Updating options: %s" %options)
        self.options = options

    def create_default_options(self):
        """ Used until options are updated with update_options
        """
        self.options = {}
        self.options['bare'] = False
        self.options['weights'] = False
        self.options["imports"] = ""
        self.options["args"] = ""
        self.options["kwargs"] = ""

    def create_julia_swap(self):
        """ Generates a list of sympy substitution tuples to sub out sympy vars
        with julia formating.

        Example
        -------
        Time update: t => _t.

        Vars update: x1 => _x[1].

        Params update: p1 => ps.p1.

        Inputs update: u1 => _inp[1].
        """
        self.julia_swap = []
        self.julia_swap.append(('t', '_t'))
        for p in self.mm.model_ps.list:
            self.julia_swap.append((p, 'ps.' + p))
        for i, v in enumerate(self.mm.model_vs.list):
            self.julia_swap.append((v, '_x[{0}]'.format(i+1)))
        for i, u in enumerate(self.mm.model_eqs['inp'].eq_symbols):
            self.julia_swap.append((u.strip(), '_inp[{0}]'.format(i+1)))

    def write_xi(self):
        return 'xi = ParametricModels.xvalues(parametricmodel)\n'

    def write_end(self):
        return 'end # module'

    ## model specific
    def write_bare_model(self):
        ret = ''
        ret += 'zerodata = ParametricModels.OLSData("%s"_zero, zero(ydata))\n' % self.name
        ret += 'bareparametricmodel = @ParametricModels.ODEModel(zerodata, %s, ic, rhs, obs, _t, (), Tuple{Symbol, Any}[])\n' % self.name
        ret += self.write_param_transforms(bare=True)
        ret += 'modelbare = Models.Model(bareparametricmodel)\n'
        return ret

    def write_imports(self):
        ret = 'module {0}_Model\n\n'.format(self.name)
        ret += 'import Models\n'
        ret += 'import ParametricModels\n'
        ret += 'using Parameters\n'
        self.logger.debug("Extra modules to import: %s" %self.options["imports"])
        if self.options["imports"] != "":

            ret += "import %s\n\n" %self.options["imports"]
        else:
            ret += "\n"
        return ret

    def write_params(self):
        ret = '@with_kw mutable struct %s{T<:Real} <: ParametricModels.AbstractParameterSpace{T} @deftype T\n' % self.name
        for p in self.mm.model_ps.dict['ps']:
            ret += '\t'
            ret += p['name']
            ret += ' = '
            ret += str(p['init_val'])
            ret += '\n'
        ret += 'end\n\n'
        return ret

    def write_inputs(self):
        ret = 'function inp(ps::%s{T}, _t) where T <: Real\n' % self.name
        ret += self.write_substitutions(self.mm.model_eqs['inp'].sbs_sym_list)
        ret += self.write_equation_return(self.mm.model_eqs['inp'].eqs_sym_list)
        return ret

    def write_data(self):
        ret = "import HDF5\n"
        ret += 'ydata = HDF5.h5read("%s", "/ydata")\n' % self.data_path.replace("\\", "\\\\")
        ret += '_t = HDF5.h5read("%s", "/t")\n' % self.data_path.replace("\\", "\\\\")
        if not self.options['weights']:
            ret += 'data = ParametricModels.OLSData("%s", ydata)\n' % self.name
        else:
            ret += 'weights = HDF5.h5read("%s", "/weights")\n' % self.data_path
            ret += 'data = ParametricModels.WLSData("%s", ydata, weights)\n' % self.name
        return ret

    def write_substitutions(self, sub_list):
        """ Given a list of substitutions, write them out prior to the return
        statement or the main equations.

        Parameters
        ----------
        sub_list: ``list``
            A list containing equation dictionaries.

        Example
        -------
        c = a + b => {"sym":  "c", "eq": "a + b"}
        """
        ret = ''
        for sub in sub_list:
            ret += '\t'
            ret += str(sub['sym'])
            ret += ' = '
            ret += julia_code(sub['eq'].subs(self.julia_swap))
            ret += '\n'
        return ret

    def write_equation_return(self, eq_list):
        """ Given a list of equations, write them out as a julia array following
        the return statement.

        Parameters
        ----------
        eq_list: ``list``
            A list containing equation dictionaries. Where each equation is
            only on the right-hand side. There should be no symbol for this
            function.

        Example
        -------
        a + b => {"sym":  "", "eq": "a + b"}
        """
        ret = '\treturn '
        ret += self.write_equation_list(eq_list)
        ret += '\nend\n\n'
        return ret

    def write_equation_list(self, eq_list):
        """ Given a list of equations, write them out as a julia array.

        Parameters
        ----------
        eq_list: ``list``
            A list containing equation dictionaries. Where each equation is
            only on the right-hand side. There should be no symbol for this
            function. The non-julia values will be subbed with julia values.

        Example
        -------
        x + b => {"sym":  "", "eq": "a + b"}
        """
        ret = 'T['
        for i, eq in enumerate(eq_list):
            ret += julia_code(eq['eq'].subs(self.julia_swap))
            if i != len(eq_list)-1:
                ret += ', '
        ret += ']'
        return ret

    def write_constants(self):
        ret = '@ParametricModels.SetConstant(parametricmodel, '
        for i, p in enumerate(self.mm.model_ps.dict['ps']):
            if p['transform'] == 'constant':
                ret += p['name']
                ret += ', '
        ret = ret[:-2]
        ret += ')\n'
        return ret

    def write_param_transforms(self, bare=False):
        if not bare:
            ret = 'for p in parametricmodel.parameters\n'
        else:
            ret = 'for p in bareparametricmodel.parameters\n'
        ret += '\tif p.s in ' + self.list_out_param_type('log') + '\n'
        ret += '\t\tp.t = exp\n'
        ret += '\t\tp.invt = log\n'
        ret += '\telseif p.s in ' + self.list_out_param_type('sinh') + '\n'
        ret += '\t\tp.t = sinh\n'
        ret += '\t\tp.invt = asinh\n'
        ret += '\tend\n'
        ret += 'end\n\n'
        return ret

    def list_out_param_type(self, p_type):
        ret = '['
        for i, p in enumerate(self.mm.model_ps.dict['ps']):
            if p['transform'] == p_type:
                ret += ':'+ p['name'] + ', '
        if len(ret) > 1:
            ret = ret[:-2]
        ret += ']'
        return ret

    def init_models_dir(self):
        """ Generates a directory: julia_scripts/models/ to save the model
        file within.
        """
        if not os.path.exists(self.dir):
            os.makedirs(self.dir)

    def save_to_file(self, script):
        """ Overwrites the current script with the given script string.

        Parameters
        ----------
        script: ``str``
            A string representation of a full julia model script.
        """
        self.logger.info("Writing script to file: %s" %self.file_path)
        self.init_models_dir()
        with open(self.file_path, "w", encoding="utf-8") as jl:
            jl.write(script)

    def parse_args(self):
        self.logger.debug("Parsing args: %s", self.options["args"])
        if self.options["args"] == "":
            args = "()"
        else:
            args = "(%s,)" %self.options["args"]
        self.logger.debug("Parsed args = %s" %args)
        return args

    def parse_kwargs(self):
        self.logger.debug("Parsing kwargs: %s", self.options["kwargs"])
        if self.options["kwargs"] == "":
            kwargs = "Tuple{Symbol, Any}[]"
        else:
            kwargs = "Tuple{Symbol, Any}["
            for kwarg in self.options["kwargs"].split(','):
                s,v = kwarg.split("=")
                kwargs += "(:%s, %s)," %(s.strip(),v.strip())
            kwargs += "]"
        self.logger.debug("Parsed kwargs = %s" %kwargs)
        return kwargs

    def find_replace_vectorized(self,string):
        d = {"\.\*": ' .* ', "\.\/": ' ./ ', "\.\^": ' .^ '}
        for item in d.keys():
            # sub item for item's paired value in string
            string = re.sub(item, d[item], string)
        return string
