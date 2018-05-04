"""
Singular Limits are often found when using the Manifold Boundary Approximation
Method. This module is built to evaluate these limits automatically. It
works for specific cases e.g. var*epsilon, var/epsilon, and combining equations.

Further work can be done to extend this class to work on a more broad range
of variable/singular limits.
"""

from sympy import solveset, Symbol, sympify, gruntz
import sympy

class SingularLimit:
    """
    Parameters
    ----------
    dae_model : ``DAEModel``
        A differential algebraic equation model.
    """
    def __init__(self, dae_model):
        self.dae = dae_model
        self.eval_limit()

    def check_var_and_epsilon(self):
        """Checks every variable to see if one is found with every instance of
        epsilon. *May also need to add check for the derivative.*

        Returns
        -------
        ``bool``
            True if one variable is found with every instance of epsilon.
        """
        eps = Symbol("epsilon")
        var_test = set([Symbol(v) for v in self.dae.model_vs.list])
        for eq_i, term_list in self.eps_eqs.items():
            for t in term_list:
                var_test = t.atoms() & var_test
        if len(var_test) == 1:
            var = list(var_test)[0]
            op = self.merge_operator(var)
            if op != "":
                subs = self.merge_subs(list(var_test), op)
                self.dae.substitute(subs)
                return True
            return False

    def merge_operator(self, var):
        """Finds the operator used between the variable and epsilon.

        Parameters
        ----------
        var : ``str``
            The variable that occurs with every instance of epsilon.

        Returns
        -------
        ``str``
            A string representation of the operator used between the variable
            and epsilon. Empty if the operators vary.
        """
        eps = Symbol("epsilon")
        mult = var * eps
        is_mult = True
        div = var/eps
        is_div = True
        for eq_i, term_list in self.eps_eqs.items():
            for t in term_list:
                if not t.has(mult):
                    is_mult = False
                if not t.has(div):
                    is_div = False
        if is_mult == is_div:
            return ""
        elif is_div:
            return "/"
        elif is_mult:
            return "*"


    def merge_subs(self, sym_vs, str_operator):
        """Combines the variables in the list with epsilon if being operated on
        by the given operator.

        Parameters
        ----------
        sym_vs : ``Sympy.Symbol``
            A list of symbolic variables (often just one variable).
        str_operator : ``str``
            The operator acting on the variable and epsilon.

        Returns
        -------
        subs : ``list``
            A list of tuples for substituting var(operator)epsilon to vartilde.
        """
        subs = []
        eps = Symbol("epsilon")
        for v in sym_vs:
            tilde = sympify(str(v)+"tilde")
            # update A => Atilde
            to_merge = sympify(str(v) + str_operator + str(eps))
            init_merge = sympify(str(v) + "_init" + str_operator + str(eps))
            subs.append((to_merge, tilde))
            # update Adot => Atildedot
            if str_operator == "*":
                # update observations
                subs.append((v, tilde))
                # update derivatives
                subs.append((sympify(str(v)+"dot"), sympify(str(tilde)+"dot")))
            elif str_operator == "/":
                subs.append((v, 0))
                subs.append((sympify(str(v)+"dot"), 0))
            subs.append((init_merge, sympify(str(v)+"_init")))
            # update A_init * epsilon => A_init
            self.dae.model_vs.update_name(str(v), str(tilde))
        return subs

    def divide_epsilon(self):
        """Checks if the majority of any equation in the model is combosed of
        the term being multiplied by epsilon. If it is the majority and there are
        no epsilon terms found in the denominator, the equation will be divided
        by epsilon.
        """
        eps = Symbol("epsilon")
        divided = 1/eps
        for index, eq in self.eps_eqs_full.items():
            div_count = 0
            mult_count = 0
            eq_divided = False
            for t in eq.expand().as_terms()[0]:
                if t[0].has(divided):
                    div_count += 1
                    eq_divided = True
                elif t[0].has(eps):
                    mult_count += 1
            if not eq_divided and len(eq.expand().as_terms())/2.0 <= mult_count:
                eq = (eq/eps).expand()
                self.dae.model_eqs['res'].eqs.divide_epsilon(index)

    def eval_limit(self):
        """Evaluates the potential singular limit.
        """
        # Find the terms containing epsilon, used to divide
        self.find_epsilon()
        self.divide_epsilon()
        # After dividing, check the terms again
        self.find_epsilon()
        # Check if merging var/eps => Singular limit
        # Will also check for var*eps => dual?
        self.check_var_and_epsilon()
        # Check if singularities are shared amongst variables
        self.combine_eqs(self.find_like_terms())
        # update all the variables
        self.transform_vars()
        # remove instabilities by multiplying by epsilon before evaluating.
        self.multiply_epsilon()

        self.dae.eval_epsilon()
        self.dae.check_var_types()
        self.dae.icd_algebraic()

    def transform_vars(self):
        """Creates all substitutions necessary for the model to be valid
        following the evaluation of a singular limit.
        """
        derivs = self.find_derivatives()
        new_var_eqs = self.new_var_equals(derivs)
        new_vars = self.find_new_var_names(len(new_var_eqs))
        self.create_new_var_subs(new_vars, new_var_eqs)
        self.create_old_to_new_vars()
        self.update_vars()
        self.sub_vars_in_res()
        self.sub_vars_in_ic()
        self.sub_vars_in_icd()
        self.sub_vars_in_obs()

    def update_vars(self):
        """Updates the variables in the model with new names.
        """
        for i, v in enumerate(self.dae.model_vs.list):
            self.dae.model_vs.update_name(v, str(self.new_var_list[i]))

    def set_fast_algebraic(self):
        """Sets the fast variable as algebraic.
        * Most likely not needed anymore.
        """
        fast = str(self.fast_dot.subs(self.dot_to_v))
        self.dae.model_vs.set_var_alg(fast)

    def sub_vars_in_obs(self):
        """Substitute the new variables into the observation function.
        """
        for i, e in enumerate(self.dae.dict['obs']['eqs']):
            # print("NEW OBS: ", e['eq'].subs(self.old_to_new))
            self.dae.model_eqs['obs'].eqs.replace_eq(i, e['eq'].subs(self.old_to_new))

    def sub_vars_in_icd(self):
        """Substitute the new variables into the initial condition derivatives
        function.
        """
        dot_to_zero = [(v[0], 0) for v in self.dot_to_v]
        for i, e in enumerate(self.dae.model_vs.list):
            e = sympify(e)
            for sub in self.new_to_old:
                if e == sub[0]:
                    new_icd = sub[1].subs(self.icd_new_to_old)
                    self.dae.model_eqs['icd'].eqs.replace_eq(i, new_icd)

    def sub_vars_in_ic(self):
        """Substitutes the new variables into the initial conditions.
        """
        new_v_to_init = []
        # Prints out any variable transformations occuring
        print("Variable Transformation: ", self.new_to_old)
        for i, e in enumerate(self.dae.dict['ic']['eqs']):
            old_init = sympify(e['eq'])
            new_init = sympify(self.new_var_list [i]).subs(self.new_to_old).subs(self.v_to_init_icd)
            self.dae.model_eqs['ic'].eqs.replace_eq(i, new_init)

    def sub_vars_in_res(self):
        """Substitutes the new variables into the residuals function.
        """
        old_to_new_dot = [(v[0].subs(self.v_to_dot), v[1].subs(self.v_to_dot)) for v in self.old_to_new]
        for i, e in enumerate(self.dae.dict['res']['eqs']):
            self.dae.model_eqs['res'].eqs.replace_eq(i, e['eq'].subs(self.old_to_new + old_to_new_dot))

    def create_old_to_new_vars(self):
        """Creates the substitution from the old variables to those newly
        defined with the singular limit.
        """
        self.old_to_new = []
        self.new_var_list = self.dae.model_vs.list
        for i, v in enumerate(self.new_to_old):
            slow_var = v[1].atoms() - set([-1, self.fast_dot.subs(self.dot_to_v)])
            slow_var = list(slow_var)[0]
            self.old_to_new.append((slow_var, solveset(self.zeros[i], slow_var).args[0]))
            self.new_var_list[self.new_var_list.index(str(slow_var))] = str(v[0])


    def create_new_var_subs(self, new_vars, new_var_eqs):
        """Creates all substitutions necessary to update different functions
        as well as for use in the algorithm.
        """
        self.all_vars = list(set(self.dae.model_vs.list + new_vars))
        self.new_derivs = [(sympify(str(new_vars[i])+"dot"), new_var_eqs[i]) for i in range(len(new_vars))]
        # define substitutions
        self.v_to_init_icd = []
        for i, e in enumerate(self.dae.dict['ic']['eqs']):
            self.v_to_init_icd.append((sympify(self.dae.model_vs.list[i]), sympify(e['eq'])))

        self.v_to_init = [(sympify(v), sympify(v+"_init")) for v in self.all_vars]
        self.v_to_dot = [(sympify(v), sympify(v+"dot")) for v in self.all_vars]
        self.init_to_v = [(sympify(v+"_init"), sympify(v)) for v in self.all_vars]
        self.dot_to_v = [(sympify(v+"dot"), sympify(v)) for v in self.all_vars]
        self.new_to_old = [(sympify(str(new_vars[i])), new_var_eqs[i].subs(self.dot_to_v)) for i in range(len(new_vars))]
        self.icd_new_to_old = []

        for i, eq in enumerate(self.dae.model_eqs['icd'].eqs.sym_list):
            self.icd_new_to_old.append((sympify(self.dae.model_vs.list[i]), eq['eq']))
        self.zeros = [(v[1] - v[0]) for v in self.new_to_old]

    def find_derivatives(self):
        """Searches the residuals for derivatives. Used to merge those derivatives
        where more than one derivative occurs in a given equation.

        Returns
        -------
        ``dict``
            A dictionary containing the equation index as the key, and a list
            of the derivatives contained in that equation as the value.
        """
        new_v_dict = {}
        for i, e in enumerate(self.dae.dict['res']['eqs']):
            new_v_dict[i] = []
            for t in sympify(e['eq']).simplify().as_terms()[0]:
                if "dot" in str(t[0]):
                    new_v_dict[i].append(t[0])
        return new_v_dict

    def new_var_equals(self, new_v_dict):
        """Counts the derivatives in each equation

        Parameters
        ----------
        new_v_dict : ``dict``
            A dictionary containing the equation index as the key, and a list
            of the derivatives contained in that equation as the value.

        Returns
        -------
        ``list``
            A list of combined derivatives. These combinations will be represented
            as a single variable after the limit is evaluated.
        """
        new_vars_equals = []
        count_dots = {}
        for dots in new_v_dict.values():
            d_combo = None
            if len(dots) >= 2:
                for d in dots:
                    ## count total derivative occurance, find fast var ##
                    if -1 in d.atoms():
                        # if negative, make it positive (for counting)
                        key = d * -1
                    else:
                        key = d
                    if key in count_dots:
                        count_dots[key] += 1
                    else:
                        count_dots[key] = 1
                    ## end count ##
                    ## extract derivatives ##
                    if d_combo == None:
                        d_combo = d
                    else:
                        d_combo = d_combo + d
                    ## end extraction ##
            if d_combo:
                new_vars_equals.append(d_combo)
        self.find_fast_var(count_dots)
        return new_vars_equals

    def find_new_var_names(self, num_vars):
        """Creates new variable names that don't already occur within the model.

        Parameters
        ----------
        num_vars : ``int``
            The number of variable names to be returned.

        Returns
        -------
        ``list``
            A list of new parameter names.
        """
        new_vars = []
        i = 1
        atoms = self.dae.atoms
        while len(new_vars) < num_vars:
            temp_var = Symbol("x_{}".format(i))
            if temp_var not in atoms and str(temp_var) not in self.dae.used_vars:
                atoms.add(temp_var)
                new_vars.append(str(temp_var))
                self.dae.used_vars.append(str(temp_var))
            i += 1
        return new_vars

    def find_fast_var(self, deriv_counts):
        """Uses the counts of derivatives to assign the variable with the
        most frequent derivative as the fast variable.

        Parameters
        ----------
        deriv_counts : ``dict``
            A dictionary mapping from derivative value to count.
        """
        fast_dot = None
        max_count = 0
        for dot, count in deriv_counts.items():
            if count > max_count:
                fast_dot = dot
                max_count = count
        self.fast_dot = fast_dot


    def combine_eqs(self, add_dict):
        """Combines the given equations within the model.

        Parameters
        ----------
        add_dict : ``dict``
            A dictionary mapping from operator to list of tuples each containg
            two values -- the equations to be operated on.

        Example
        -------
            {"+": [(0, 1)]}: Add equation 0 to equation 1.
        """
        for combine in add_dict["+"]:
            res1 = self.dae.model_eqs['res'].eqs.sym_list[combine[0]]['eq']
            res2 = self.dae.model_eqs['res'].eqs.sym_list[combine[1]]['eq']
            self.dae.model_eqs['res'].eqs.replace_eq(combine[1], res1 + res2)
        for combine in add_dict["-"]:
            res1 = self.dae.model_eqs['res'].eqs.sym_list[combine[0]]['eq']
            res2 = self.dae.model_eqs['res'].eqs.sym_list[combine[1]]['eq']
            self.dae.model_eqs['res'].eqs.replace_eq(combine[1], res1 - res2)

    def find_epsilon(self):
        """Searches the residuals function for all terms that epsilon is found
        in. Creates a dictionary mapping from equation index to list of terms
        containing epsilon found in that equation.
        """
        eps = set([Symbol("epsilon")])
        res = self.dae.model_eqs['res']
        self.eps_eqs_full = {}
        self.eps_eqs = {}
        self.eps_neg_eqs = {}
        for i, eq in enumerate(res.eqs.sym_list):
            if eq['eq'].has(Symbol("epsilon")):
                self.eps_eqs_full[i] = eq['eq']
            terms, neg_terms = self.extract_epsilon_terms(eq['eq'])
            if len(terms) > 0:
                self.eps_eqs[i] = terms
                self.eps_neg_eqs[i] = neg_terms

    def extract_epsilon_terms(self, eq):
        """Extracts all epsilon terms from a given equation.

        Parameters
        ----------
        eq : ``Sympy Equation``
            A symbolic form of an equation, potentially containin epsilon.

        Returns
        -------
        terms : ``list``
            The list of terms that contain epsilon found in the equation.
        negative_terms : ``list``
            The list of terms that contain epsilon found in the equation,
            where each term has been multiplied by -1.
        """
        terms = []
        negative_terms = []
        # print("EQ: ", eq)
        # print("FACTOR: ", eq.expand())
        for t in eq.expand().as_terms()[0]:
            # print("TERM: ", t[0].factor())
            if t[0].has(Symbol("epsilon")):
                terms.append(t[0])
                negative_terms.append(t[0]*-1)
        return terms, negative_terms

    def find_like_terms(self):
        """Checks each list of terms to find equations that have exact
        (positive or negative) lists of terms.

        Returns
        -------
        to_combine : ``dict``
            A dictionary mapping from operator to a list of tuples directing
            which equations should be combined together.
        """
        keys_1 = list(self.eps_eqs.keys())
        keys_2 = list(self.eps_eqs.keys())
        to_combine = {"+": [], "-": []}
        for key in keys_1:
            keys_2.remove(key)
            for key2 in keys_2:
                if set(self.eps_eqs[key]) == set(self.eps_eqs[key2]):
                    keys_1.remove(key2)
                    to_combine["-"].append(tuple((key, key2)))
                elif set(self.eps_eqs[key]) == set(self.eps_neg_eqs[key2]):
                    keys_1.remove(key2)
                    to_combine["+"].append(tuple((key, key2)))
        return to_combine

    def multiply_epsilon(self):
        """Looks for epsilon in the denominator of the equation. If found,
        multiplies that equation by epsilon to remove instabilities.
        """
        for i, eq in enumerate(self.dae.model_eqs['res'].eqs.sym_list):
            if eq['eq'].has(Symbol("epsilon")):
                g_limit = gruntz(eq['eq'], Symbol("epsilon"), 0)
                if len(set([sympy.numbers.Infinity(), sympy.numbers.NegativeInfinity()]) & g_limit.atoms()) != 0:
                    self.dae.model_eqs['res'].eqs.multiply_epsilon(i)
        for i, eq in enumerate(self.dae.model_eqs['icd'].eqs.sym_list):
            g_limit = gruntz(eq['eq'], Symbol("epsilon"), 0)
            if len(set([sympy.numbers.Infinity(), sympy.numbers.NegativeInfinity()]) & g_limit.atoms()) != 0:
                self.dae.model_eqs['icd'].eqs.multiply_epsilon(i)
