"""
All pieces of a model. This contains Param, Params, Var,
Vars, Eq, Eqs, and EqFull.

Any model dictionary will be parsed into these individual pieces.
"""

import random
from sympy import sympify, Symbol, gruntz, latex
import sympy
from copy import deepcopy

P_ATTR = ["name", "init_val", "transform"]
VALID_TRANSFORMS = ["identity", "log", "constant", "sinh"]

class Param:
    """Base Parameter Class.
    """
    def __init__(self, **kwargs):
        """

        Parameters
        ----------
        name : ``str``
            The name of the parameter.
        init_val : ``float``
            The initial parameter value.
        transform: ``str``
            Transformation applied to the parmater. Valid transforms:
            'identity','log', 'sinh', or 'constant'.
        """
        self.set_name(kwargs.get("name", "p"+str(random.randint(0, 9999999))))
        self.set_init_val(kwargs.get("init_val", 1))
        self.set_transform(kwargs.get("transform", "identity"))

    def set_name(self, name):
        """Updates the name.

        Parameters
        ----------
        name : ``str``
            The name of the parameter.
        """
        try:
            self.name = str(name)
            self.valid_name = True
        except Exception as E:
            print("INVALID PARAMETER ATTR: \"name\": ", E)
            self.valid_name = False

    def set_init_val(self, init_val):
        """Updates the initial value.

        Parameters
        ----------
        init_val : ``float``
            The initial parameter value.
        """
        try:
            self.init_val = float(init_val)
            self.valid_init = True
        except Exception as E:
            print("INVALID PARAMETER ATTR: \"init_val\": ", E)
            self.valid_init = False

    def set_transform(self, transform):
        """Updates the transform value.

        Parameters
        ----------
        transform: ``str``
            Transformation applied to the parmater. Valid transforms:
            'identity','log', 'sinh', or 'constant'.
        """
        try:
            temp = str(transform).lower()
            VALID_TRANSFORMS.index(temp)
            self.transform = temp
            self.valid_trans = True
        except Exception as E:
            print("INVALID PARAMETER ATTR: \"transform\": ", E)
            self.valid_trans = False

    def __str__(self):
        """

        Returns
        -------
        name : ``str``
            The name of the parameter.
        """
        return self.name

    @property
    def dict(self):
        """``dict``: param = {'name': 'p1', 'init_val', 1.0, 'transform': 'log'}"""
        if self.valid_name and self.valid_init and self.valid_trans:
            return {attr: getattr(self, attr) for attr in P_ATTR}
        else:
            return {}


class Params:
    """A class containing all model parameters as ``Param``.
    """
    def __init__(self, p_list):
        """

        Parameters
        ----------
        p_list : ``list``
            List of parameter dictionaries.

        Example
        -------
        param_list = [{'name': 'p1', 'init_val', 1.0, 'transform': 'log'}, ...]
        """
        self.ps = []
        for i, p in enumerate(p_list):
            self.ps.append(Param(**p))

    @property
    def dict(self):
        """``dict``: ps_dict = {"ps": [{'name': 'p1', 'init_val', 1.0, 'transform': 'log'}]}"""
        return {"ps": [p.dict for p in self.ps]}

    def update_index_transform(self, index, t):
        """Sets the parameter's transformation at `index` to `t`.

        Parameters
        ----------
        index : ``int``
            The index of the parameter to be updated.
        t : ``str``
            The transformation to change the given parameter to.
        """
        self.ps[index].set_type(t)

    def update_index_init(self, index, init_val):
        """Sets the parameter's initial value at `index` to `init_val`.

        Parameters
        ----------
        index : ``int``
            The index of the parameter to be updated.
        init_val : ``float``
            The initial value.
        """
        self.ps[index].set_init_val(init_val)

    def update_index_name(self, index, name):
        """Sets the parameter's name at `index` to `name`.

        Parameters
        ----------
        index : ``int``
            The index of the parameter to be updated.
        init_val : ``float``
            The initial value.
        """
        self.ps[index].set_name(name)

    def __len__(self):
        """

        Returns
        -------
        len : ``int``
            The total number of parameters.
        """
        return len(self.symbols)

    @property
    def list(self):
        """``list``: A list of parameter names."""
        return [p.name for p in self.ps]

    @property
    def non_constants(self):
        """``list``: A list of *non-constant* parameter names."""
        return [p.name for p in self.ps if p.transform != "constant"]

    @property
    def symbols(self):
        """``list``: A list of *non-constant* parameter SymPy symbols."""
        return set([Symbol(p.name) for p in self.ps if p.transform != "constant"])

    def update_params(self, old_params, new_params):
        """Renames each parameter found in `old_params` to the
        name in `new_params`.

        Parameters
        ----------
        index : ``int``
            The index of the parameter to be updated.
        init_val : ``float``
            The initial value.
        """
        # update the parameter init vals too?
        for i in range(len(old_params)):
            self.ps[self.list.index(old_params[i])].name = new_params[i]

    def remove_epsilon(self):
        """Removes any parameter named 'epsilon'.
        """
        self.ps.pop(self.list.index("epsilon"))


VALID_VAR_TYPES = ['algebraic', 'dynamic']
V_ATTR = ['name', 'type']
class Var:
    """Base Variable Class.
    """
    def __init__(self, **kwargs):
        """

        Parameters
        ----------
        name : ``str``
            The name of the variable.
        type : ``str``
            The variable type. Either 'algebraic' or 'dynamic'. Defaults to 'dynamic'.
        """
        self.set_name(kwargs.get("name", "v"+str(random.randint(0, 9999999))))
        self.set_type(kwargs.get("type", "dynamic"))

    def set_name(self, name):
        """

        Parameters
        ----------
        name : ``str``
            The name of the variable.
        """
        try:
            self.name = str(name)
            self.valid_name = True
        except Exception as E:
            print("INVALID VARIABLE ATTR: \"name\": ", E)
            self.valid_name = False

    def set_type(self, t):
        """

        Parameters
        ----------
        t : ``str``
            The variable type. Either 'algebraic' or 'dynamic'.
            Defaults to 'dynamic'.
        """
        try:
            temp = str(t).lower()
            VALID_VAR_TYPES.index(temp)
            self.type = temp
            self.valid_type = True
        except Exception as E:
            print("INVALID VARIABLE ATTR: \"type\": ", E)
            self.valid_type = False

    def __str__(self):
        """

        Returns
        -------
        name : ``str``
            The name of the variable.
        """
        return self.name

    @property
    def dict(self):
        """``dict``: var = {'name': 'x1', 'type': 'dynamic'}"""
        if self.valid_name and self.valid_type:
            return {attr: getattr(self, attr) for attr in V_ATTR}
        else:
            return {}


class Vars:
    """A class containing all model variables as ``Var``.
    """
    def __init__(self, v_list):
        """

        Parameters
        ----------
        v_list : ``list``
            List of variable dictionaries.

        Example
        -------
        var_list = [{'name': 'v1', 'type', 'dynamic'}, ...]
        """
        self.vs = []
        for i, v in enumerate(v_list):
            self.vs.append(Var(**v))
#             setattr(self, v['name'], self.vs[-1]) # will probably reference parameters by index in list, not name

    @property
    def dict(self):
        """``dict``: vs_dict = {"vs": [{'name': 'v1', 'type', 'dynamic'}]}"""
        return {"vs": [v.dict for v in self.vs]}

    def set_index_alg(self, index):
        """Updates the variable at the given index to 'algebraic'.

        Parameters
        ----------
        index : ``int``
            The index of the variable to be updated.
        """
        self.vs[index].set_type("algebraic")

    def set_index_dyn(self, index):
        """Updates the variable at the given index to 'dynamic'.

        Parameters
        ----------
        index : ``int``
            The index of the variable to be updated.
        """
        self.vs[index].set_type("dynamic")

    def update_name(self, old_name, new_name):
        """Renames a single variable from `old_name` to `new_name`.

        Parameters
        ----------
        old_name : ``str``
            The name to be replaced.
        new_name : ``str``
            The new name used in place of old_name.
        """
        self.vs[self.var_index(old_name)].set_name(new_name)

    def __len__(self):
        """

        Returns
        -------
        len : ``int``
            The number of variables in the list.
        """
        return len(self.vs)

    def var_index(self, var_name):
        """Return the index of the given variable name.

        Parameters
        ----------
        var_name : ``str``
            The name of the variable to be found.

        Returns
        -------
        index : ``int``
            The index of the variable with the given name.
        """
        return self.list.index(var_name)

    def set_var_alg(self, var_name):
        """Update the variable with `var_name` as name to 'algebraic'.

        Parameters
        ----------
        var_name : ``str``
            The name of the variable to be updated.
        """
        self.set_index_alg(self.var_index(var_name))

    @property
    def list(self):
        """``list``: A list of variable names."""
        return [v.name for v in self.vs]


class Eq:
    """The Base Equation Class.
    May contain two parts, a symbol and an equation.

    Example
    -------
    a = b + c => symbol: a, equation: b + c

    If the input as an '=', the left side will be the symbol, the right side
    will be the equation.
    """
    def __init__(self, str_eq, equals=False):
        """Parses the str_eq into symbol/equation.

        Parameters
        ----------
        str_eq : ``str``
            The equation in string format.
        equals : ``bool``
            True if the str_eq contains '='.
        """
        self.equals = equals
        if self.equals:
            temp_eq = str_eq.replace(" ", "").split("=")
            self.symbol = temp_eq[0]
            self.eq = temp_eq[1]
        else:
            self.symbol = None
            self.eq = str_eq

    def change_to_DAE(self, var):
        """Subtracts the given variable from the right hand side.

        Used to move derivatives to the right hand side.

        Parameters
        ----------
        var : ``SymPy.Symbol`` or ``str``
            The variable to be subtracted from the right hand side, often a derivative.
        """
        self.eq = self.eq + "-" + str(var)
        return self.eq

    @property
    def latex(self):
        """``str``: The latex string of the equation."""
        return latex(self.sympy)

    @property
    def sympy(self):
        """``SymPy Symbol``:The equation as a SymPy object."""
        return sympify(self.eq).expand()

    @property
    def atoms(self):
        """``set``: The set of all SymPy.Symbol objects in the equation."""
        return self.sympy.atoms()

    def __str__(self):
        """
        Returns
        -------
        eq : ``str``
            The string representation of the equation.
        """
        if self.symbol:
            return str(self.symbol) + " = " + str(self.eq)
        else:
            return str(self.eq)

    @property
    def dict(self):
        """``dict``: Equation dictionary containing SymPy objects."""
        return {"sym": sympify(self.symbol), "eq": self.sympy}

    @property
    def str_dict(self):
        """``dict``: a = b + c => {"sym": "a", "eq": "b+c"}."""
        return {"sym": self.symbol, "eq": self.sympiy}

    def substitute(self, substitutions):
        """Substitutes a list of SymPy substitutions into the equation,
        including the symbol.

        Parameters
        ----------
        substitutions : ``list``
            A list of tuples used to subtitute into the equation.
        """
        if self.symbol:
            self.symbol = str(sympify(self.symbol).subs(substitutions))
        self.eq = str(sympify(self.eq).expand().subs(substitutions).simplify())

    def multiply_epsilon(self):
        """Multiply the right hand side by 'epsilon'.
        """
        self.eq = str(sympify(self.eq)*sympify("epsilon"))
        # print("SELF EQ:", self.eq)

    def divide_epsilon(self):
        """Divide the right hand side by 'epsilon'.
        """
        self.eq = str(sympify(self.eq)/sympify("epsilon"))

    def eval_epsilon(self):
        """Take the limit as the parameter epsilon goes to zero.
        """
        if self.symbol:
            self.symbol = gruntz(sympify(self.symbol).simplify(), Symbol("epsilon"), 0)
        self.eq = gruntz(sympify(self.eq).simplify(), Symbol("epsilon"), 0)


class Eqs:
    """A class containing a list of equations **or** substitutions as
    ``Eq``.
    """
    def __init__(self, str_eq_list, equals=False, subs=False):
        """

        Parameters
        ----------
        str_eq_list : ``list``
            A list of equations represented as strings.
        equals : ``bool``
            True if there are '=' in the strings.
        subs : ``bool``
            True of the given list is used as substitutions.
        """
        self.sbs = subs
        self.eqs = []
        self.equals = equals
        for e in str_eq_list:
            self.eqs.append(Eq(e, self.equals))

    @property
    def latex(self):
        """``list``:A list of the equations in latex formatting."""
        return [eq.latex for eq in self.eqs]

    @property
    def dict(self):
        """``dict``: eqs_dict = {"sbs": [{'sym': 'a', 'eq': 'b + c'}]} as sympy equations."""
        if self.sbs:
            return {"sbs": [e.dict for e in self.eqs]}
        else:
            return {"eqs": [e.dict for e in self.eqs]}

    @property
    def str_dict(self):
        """``dict``: eqs_dict = {"sbs": [{'sym': 'a', 'eq': 'b + c'}]} as strings."""
        if self.sbs:
            return {"sbs": [e.str_dict for e in self.eqs]}
        else:
            return {"eqs": [e.str_dict for e in self.eqs]}

    @property
    def atoms(self):
        """``set``: A set of all SymPy Symbols in all equations."""
        ret = set([])
        for e in self.eqs:
            ret = ret | e.atoms
        return ret

    @property
    def sym_list(self):
        """``list``:A list of dictionaries containing the SymPy symbolic equations."""
        return [eq.dict for eq in self.eqs]

    def replace_eq(self, index, eq):
        """Replace the `eq` at the given `index`.

        Parameters
        ----------
        index : ``int``
            The index of the equation to replace.
        eq : ``str``
            The string representation of the new equation.
        """
        self.eqs[index] = Eq(eq, self.equals)
        # print("NEW EQ", self.eqs[index])

    @property
    def list(self):
        """``list``:A list of string representation of the equations."""
        return [str(eq) for eq in self.eqs]

    def substitute(self, substitutions):
        """Substitutes a list of SymPy `substitutions` into each equation.
        """
        for e in self.eqs:
            e.substitute(substitutions)

    def multiply_epsilon(self, index):
        """Multiply the equation at `index` by 'epsilon'.
        """
        self.eqs[index].multiply_epsilon()

    def divide_epsilon(self, index):
        """Divide the equation at `index` by 'epsilon'.
        """
        self.eqs[index].divide_epsilon()

    def eval_epsilon(self):
        """Evaluate the limit as epsilon goes to zero for each equation.
        """
        for e in self.eqs:
            e.eval_epsilon()

    @property
    def left_hand_symbols(self):
        """``list``:A list of equation symbols (the left hand side of '=')."""
        return [e.symbol for e in self.eqs if e.symbol]

    def drop_equation(self, symbol):
        """Removes the equation with the given 'symbol'.

        Example
        -------
        a = b + c => [{'sym': a, 'eq': b + c}]

        drop_equation(a) => []
        """
        for i in range(len(self.eqs)):
            if str(self.eqs[i].symbol) == str(symbol):
                self.eqs.pop(i)
                break

class EqFull:
    """This class contains both Substitutions and Equations for a given
    equation types.

    e.g. OBS, IC, RHS, RES, etc.
    """
    def __init__(self, eq_type, **kwargs):
        """
        Parameters
        ----------
        eq_type : ``str``
            The type of equations.
        sbs : ``list``
            A list of substitutions, represented as strings.
        eqs : ``list``
            A list of equations, represented as strings.
        """
        self.set_eq_type(eq_type)
        self.sbs = Eqs(kwargs["sbs"], equals=True, subs=True)
        if self.type == "inp":
            self.eqs = Eqs(kwargs["eqs"], equals=True)
        else:
            self.eqs = Eqs(kwargs["eqs"])

    def check_subs(self):
        """Looks for the 'sym' in each substitution to be contained in the
        equations. If it is not contained in the equations, it is removed.
        """
        for i, s in enumerate(self.sbs.left_hand_symbols):
            s = sympify(s)
            if s in self.eqs.atoms:
                print(s)
            else:
                self.sbs.drop_equation(s)

    @property
    def latex(self):
        """``dict``:{"eq_type": {"sbs": [latex_sb, ...], "eqs": [latex_eq, ...]}}"""
        return {self.type: {'sbs': self.sbs.latex, 'eqs': self.eqs.latex}}

    def set_eq_type(self, t):
        """Updates the equation type.

        Parameters
        ----------
        t : ``str``
            The type of equations: 'obs', 'ic', 'rhs', 'res', etc.
        """
        self.type = t

    @property
    def atoms(self):
        """``set``:A set of all SymPy Symbols found in all equations."""
        return self.sbs.atoms | self.eqs.atoms

    @property
    def dict(self):
        """``dict``:{"eq_type": {"sbs": [sym_sb, ...], "eqs": [sym_eq, ...]}}"""
        return {self.type: {**self.sbs.dict, **self.eqs.dict}}

    @property
    def str_dict(self):
        """``dict``:{"eq_type": {"sbs": [str_sb, ...], "eqs": [str_eq, ...]}}"""
        return {self.type: {'sbs': self.sbs.list, 'eqs': self.eqs.list}}

    def substitute(self, substitutions):
        """Substitute a list of SymPy substitutions into all sbs and eqs.

        Parameters
        ----------
        substitutions : ``list``
            A list of tuples used for SymPy substitutions.
        """
        self.sbs.substitute(substitutions)
        self.eqs.substitute(substitutions)

    def eval_epsilon(self):
        """Evaluate epsilon for all sbs and eqs.
        """
        self.sbs.eval_epsilon()
        self.eqs.eval_epsilon()

    @property
    def sbs_sym_list(self):
        """``list``:A list of symbolic sbs."""
        return self.sbs.sym_list

    @property
    def eqs_sym_list(self):
        """``list``:A list of symbolic eqs."""
        return self.eqs.sym_list

    @property
    def eq_symbols(self):
        """``list``:A list of symbolic left hand side symbols."""
        return self.eqs.left_hand_symbols
