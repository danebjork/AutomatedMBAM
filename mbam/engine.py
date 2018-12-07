"""Manages many iteration of MBAM.
"""

from .modeling import *
from .iteration import Iteration
from .parsing import *
from .mongo import MMongo
from sympy import Symbol, latex, sympify
import copy


class Engine:
    """
    Parameters
    ----------
    model_dict : ``dict``
        A dictionary containing all the model information.
    data_path : ``str``
        The full path to the hdf5 data file for the model.
    """
    def __init__(self, model_dict, data_path):
        self.data_path = data_path
        self.mongo = MMongo()
        if model_dict['type'].lower() == 'ode':
            self.model = ODE(model_dict)
            self.model = self.model.to_dae()
        elif model_dict['type'].lower() == 'dae':
            self.model = DAE(model_dict)
        self.model_id = self.mongo.save_model(self.model)
        self.curr_model = self.model
        self.curr_id = self.model_id

    
    def run(self, printing=False):
        """Runs the geodesic, infers the limit, attempts to evaluate the limit.
        Continues to repeat the process until a failure.

        Parameters
        ---------
        printing : ``bool``
            Prints out each new model in latex formating if True.
        """
        for i in range(len(self.curr_model.model_ps)):
            self.curr_iter = Iteration(self.curr_model, self.curr_id, self.data_path)
            self.curr_iter.write_model_script(self.curr_iter.julia.options)  # create model.jl file
            if self.curr_iter.auto_run():
                print("PASS!")
                self.curr_model = self.curr_iter.N_minus_1
                self.curr_id = self.curr_iter.N_minus_1_id
                if printing:
                    self.print_latex(self.curr_iter.limits)
            else:
                print("FAIL on Model: ", self.curr_id)
                break

    def apply_limits(self, limit_list, printing=False):
        """Applies a list of given limits. No geodesic will be run.

        Parameters
        ----------
        limit_list : ``list``
            A list of dictionaries representing limits. Each dictionary maps
            from a parameter to a limit.
        printing : ``bool``
            Prints out each new model in latex formating if True.
        """
        for limit in limit_list:
            self.curr_iter = Iteration(self.curr_model, self.curr_id, self.data_path)
            if self.curr_iter.apply_limits(limit):
                print("PASS!")
                self.curr_iter.save_iteration()
                self.curr_model = self.curr_iter.N_minus_1
                if printing:
                    self.print_latex(limit)
                self.curr_id = self.curr_iter.N_minus_1_id
            else:
                print("FAIL on Model: ", self.curr_id)
                break

    def print_latex(self, limit):
        """Prints out a latex version of the current model and the limit
        that was evaluated.

        Parameters
        ----------
        limit : ``dict``
            The limit dictionary that was just evaluated.
        """
        model = copy.deepcopy(self.curr_model)
        print(self.print_limit(limit))
        # model.substitute(label_subs)
        print(model.latex)

    def print_limit(self, limit):
        """Parses the given limit into a latex equation.

        Parameters
        ----------
        limit : ``dict``
            A dictionary containing limits -- a mapping from parameters to
            limits.
        """
        to_ret = "$$"
        for key, val in limit.items():
            to_ret += sympy.latex(sympy.sympify(key))
            to_ret += " \\to"
            if val == "zero":
                to_ret += " 0, "
            elif val == "inf":
                to_ret += " \\infty, "
        to_ret = to_ret[:-2] + "$$"
        return to_ret
