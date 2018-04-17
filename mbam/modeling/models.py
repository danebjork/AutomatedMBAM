"""
A collection of model types: Base, Funciton, ODE, and DAE.

Base is the parent class for the other model types.
"""

from .elements import *


FUNC_EQ_TYPES = ['inp', 'f']
ODE_EQ_TYPES = ['inp', 'rhs', 'obs', 'ic']
DAE_EQ_TYPES = ['inp', 'res', 'obs', 'ic', 'icd']

# Add functions: Apply Ftheta (maybe just substitution, define pre substitution in MBAM Iteration?), Rename Params (to and back), Rename Vars (to and back), Unapply Fthetas
class Base:
    """The Base Model Class.
    """
    def __init__(self, model_dict):
        """Parses the parameters, variables, and initializes the equations dict.
        """
        self.type = model_dict['type'].lower()
        self.base_name = model_dict['name']
        self.name = model_dict['name']
        self.clss = model_dict['class'].lower()
        self.model_ps = Params(model_dict['ps'])
        self.model_vs = Vars(model_dict['vs'])
        self.model_eqs = {}

    def __str__(self):
        """

        Returns
        -------
        dict_str : ``str``
            The model dictionary cast as a string.
        """
        return str(self.dict)

    def update_name(self, hasse_child_num):
        """Creates a new name for a child off the base name inherited from
        the parent.

        Parameters
        ----------
        hasse_child_num : ``int``
            The number of children the parent model has.
        """
        self.name = self.base_name + "_P"+ str(len(self.model_ps)) + "H" + str(hasse_child_num)

    def check_subs(self):
        """Checks each equation type to make sure the substitutions listed are used
        in the equations. Deletes unused substitutions.
        """
        for eq in self.model_eqs.values():
            eq.check_subs()

    @property
    def latex(self):
        """
        Returns
        -------
        latex_str : ``str``
            The latex string to be used for publications.
        """
        if self.type == "dae":
            to_str = ""
            # to_str += "N = " + str(len(self.model_ps)) + "\n"
            to_str += "\\begin{equation} \n"
            to_str += "\\begin{split} \n"
            for i, eq_latex in enumerate(self.model_eqs['res'].eqs.latex):
                to_str += "& "
                to_str += "\\textrm{%s: }" % str(i+1)
                to_str += eq_latex + "\\\\ \n"
            to_str += "\\end{split} \n"
            to_str += "\\end{equation} \n"
            return to_str
        return ""

    @property
    def latex_eqs(self):
        """

        Returns
        -------
        latex_dict : ``dict``
            The latex version of each of the model's equations.
        """
        temp = {}
        for eq_key in self.model_eqs:
            temp = {**temp, **self.model_eqs[eq_key].latex}
        return temp

    @property
    def atoms(self):
        """``set``:All SymPy Symbols contained inside all of the model's equations."""
        ret = set([])
        for eq_list in self.model_eqs.values():
            ret = ret | eq_list.atoms
        return ret

    @property
    def str_dict(self):
        """``dict``:The dictionary representation of the model with all values cast
        as strings."""
        temp = {"type": self.type, "name": self.name, "class": self.clss}
        temp = {**temp, **self.model_ps.dict, **self.model_vs.dict}
        for eq_key in self.model_eqs:
            temp = {**temp, **self.model_eqs[eq_key].str_dict}
        return temp

    @property
    def dict(self):
        """``dict``:The dictionary representation of the model with equations as
        symbolic equations."""
        temp = {"type": self.type, "name": self.name}
        temp = {**temp, **self.model_ps.dict, **self.model_vs.dict}
        for eq_key in self.model_eqs:
            temp = {**temp, **self.model_eqs[eq_key].dict}
        return temp

    def substitute(self, substitutions):
        """Substitute the list of substitutions into all model equations.

        Parameters
        ----------
        substitutions : ``list``
            A list of tuples for SymPy substitution.
        """
        for eq_list in self.model_eqs.values():
            eq_list.substitute(substitutions)

    def update_params(self, old_p, new_p):
        """Update the model's parameters from `old_p` to `new_p`.

        Paramters
        ---------
        old_p : ``list``
            The list of old parameters.
        new_p : ``list``
            The list of new parameters.
        """
        self.model_ps.update_params(old_p, new_p)

    def eval_epsilon(self):
        """Evaluate the limit as 'epsilon' goes to zero for all equations in the
        model.
        """
        for eq_list in self.model_eqs.values():
            eq_list.eval_epsilon()
        self.model_ps.remove_epsilon()

    @property
    def all_params_in_eqs(self):
        """``bool``:True if all non-constant parameters are found in the model."""
        return self.model_ps.symbols & self.atoms == self.model_ps.symbols

    @property
    def check_eqs_finite(self):
        """``bool``:True if there are no infinity or negative infinity values in the model."""
        return len(set([sympy.numbers.Infinity(), sympy.numbers.NegativeInfinity()]) & self.atoms) == 0

    def is_valid(self):
        """Checks if all parameters are in equation, and all values finite.
        ***Needs to check if epsilon is gone!

        Returns
        -------
        valid : ``bool``
            True if the model is a valid model.
        """
        eps = Symbol("epsilon")
        return self.all_params_in_eqs & self.check_eqs_finite & (eps not in self.atoms)

    def check_var_types(self):
        for v in self.model_vs.list:
            dot = sympify(str(v) + "dot")
            if dot not in self.atoms:
                # print("NO DERIVATIVE: ", dot)
                self.model_vs.set_var_alg(str(v))

class Function(Base):
    """A Class for models containing only algebraic functions.

    Not really used...
    """
    def __init__(self, model_dict):
        super().__init__(model_dict)
        for t in FUNC_EQ_TYPES:
            self.model_eqs[t] = {}
            self.model_eqs[t] = EqFull(t, **model_dict[t])


class ODE(Base):
    """Ordinary Differential Equations Model Class
    """
    def __init__(self, model_dict):
        """Intializes the Base, and loads in ODE specific equations.

        Parameters
        ----------
        model_dict : ``dict``
            A dictionary containing a full model.
        """
        super().__init__(model_dict)
        for t in ODE_EQ_TYPES:
            self.model_eqs[t] = {}
            self.model_eqs[t] = EqFull(t, **model_dict[t])

    def deriv_name(self, var_name):
        """Inserts 'dot' between characters and the first ``int`` found in the name.

        Parameters
        ----------
        var_name : ``str``
            A variable name to altered to a derivative name.

        Returns
        -------
        new_var : ``str``
            A derivative name with dot inserted.
        """
        # new_var = ""
        # added = False
        # for i, c in enumerate(var_name):
        #     try:
        #         int(c)
        #         if not added:
        #             new_var += "dot"
        #             added = True
        #         new_var += c
        #     except:
        #         new_var += c
        # if not added:
        #     new_var += "dot"
        return var_name + "dot"

    def to_dae(self):
        """Converts the current ODE into a DAE.

        Subtracts the derivatives from the RHS of the ODE to create RES.
        Creates ICD's based off the RHS equations. Then substitutes
        the variables in the ICD with its corresponding initial condition.

        Returns
        -------
        dae : ``DAE``
            The equivalent DAE representation of the current ODE.
        """
        self.dae_var_to_ic()
        to_dae = deepcopy(self)
        to_dae.model_eqs['icd'] = deepcopy(to_dae.model_eqs['rhs'])
        to_dae.model_eqs['icd'].set_eq_type("icd")
        to_dae.model_eqs['icd'].substitute(self.dae_icd_subs)
        for i, eq in enumerate(to_dae.model_eqs['rhs'].eqs.eqs):
            eq.change_to_DAE(self.deriv_name(to_dae.model_vs.vs[i].name))
        to_dae.model_eqs['rhs'].type = "res"
        to_dae.type = "dae"
        to_dae.model_eqs['res'] = to_dae.model_eqs.pop('rhs')
        return DAE(to_dae.str_dict)

    def dae_var_to_ic(self):
        """Create a list of substitutions for converting from ODE RHS functions
        to ICD's. This will be used to substitute each variable for its
        initial cond.

        Example
        -------
        subs = [(var[0], ic[0]), ..., (var[n], ic[n])]
        """
        self.dae_icd_subs = []
        for i, v in enumerate(self.model_vs.list):
            self.dae_icd_subs.append((Symbol(v), sympify(self.model_eqs['ic'].eqs.list[i])))

class DAE(Base):
    """Differential Algebraic Equations Model Class.
    """
    def __init__(self, model_dict):
        """Creates Base as well as DAE specific equations.
        """
        super().__init__(model_dict)
        for t in DAE_EQ_TYPES:
            self.model_eqs[t] = {}
            self.model_eqs[t] = EqFull(t, **model_dict[t])

    def icd_algebraic(self):
        for i, v in enumerate(self.model_vs.dict['vs']):
            if v['type'] == 'algebraic':
                self.model_eqs['icd'].eqs.replace_eq(i, 0)
