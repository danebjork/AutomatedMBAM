"""
Given a set of limits, return all currently templated possibilities for
a reparameterization. Reparameterization is the first tool to use when
attempting to evaluate a model at a limit and remove a single parameter.

This module uses combinatorics to create possible reparameterizations using
the current limit, and templates pulled from the database. While there
may be lots of possibilities in the reparameterizations, only one valid model
needs to be returned.
"""

from sympy import sympify, solveset, Symbol
import itertools
import random

    # input: dictionary of limits {"param_name": "limit", etc.}
    # key_legend: dictionary of limits to indexes {"zero": 0, "inf": 1, etc...} corresponding to (0, 0, etc.) as template key

class Reparam:
    """Creates all possible fthetas given the limit, the legend for the limit
    template key, and filtering with the model class.
    """
    # creates all possible ftheta combos
    # uses tempaltes from database and current limits
    def __init__(self, limits, key_legend, model_class=None):
        """
        Parameters
        ----------
        limits : ``dict``
            A dictionary with key: parameter_name, value: limit_type.
        key_legend : ``dict``
            A dictionary found in the database. Maps limit type to template key
            index.
        model_class : ``str``
            Model class used to filter templates.

        Example
        -------
        limit = {"p1": "zero", "p2": "inf"}

        key_legend = {"zero": i, "inf": j}

        template key = (i, j) => (0, 2)

        0 -> number of zero limits in the template.

        2 -> number of infinity limits in the template.
        """
        self.limit_to_index = key_legend
        self.model_class = model_class
        self.label_subs = [("+", "_plus_"), ("-", "_minus_"), ("*", "_"), ("/", "_over_")]
        self.index_to_limit = {v: k for k, v in key_legend.items()}
        self.ls = limits
        self.fthetas = {k:[] for k,v in self.ls.items()}
        self.count_limits()

    def get_fthetas(self, e_temp, f_temp):
        """Finds all the potential ftheta combinations.

        Parameters
        ----------
        e_temp : ``list``
            List of templates that evaluate to zero.
        f_temp : ``list``
            List of templates that evaluate to a non-zero finite value.

        Returns
        -------
        valid_fthetas : ``list``
            A list of ftheta dictionaries.

        Example
        -------
        ftheta = {"theta": "p1", "limit": "inf", "tilde": "epsilon", "f": "1/p1"}
        """
        self.eps_poss = self.fill_template(e_temp, epsilon=True)
        self.finite_poss = self.fill_template(f_temp)
        self.filter_fthetas()
        return self.valid_fthetas

    def filter_fthetas(self):
        """Creates all possible ftheta combinations for the given limit, then
        filters out he invalid fthetas.

        See in-line comments for details.
        """
        # create ALL possible ftheta combinations
        total = list(itertools.product(*self.fthetas.values()))
        # store the ones deemed valid here:
        self.valid_fthetas = []
        # used to make sure function sets are not repeated
        all_fs = []
        for t in total:
            # count the total amount of epsilons, there should only be one
            epsilon_count = 0
            # make sure parameter names aren't duplicated (would make for a faulty ftheta)
            tildes = set([])
            # make sure all the functions have not been added before. Duplicates the work.
            fs = set([])
            for i in t:
                # add up all the items, keep track of what exists already
                tildes.add(i['tilde'])
                fs.add(i['f'])
                if i['tilde'] == "epsilon":
                    epsilon_count += 1
                if epsilon_count > 1:
                    break
            if epsilon_count != 1 or len(tildes) != len(self.ls) or fs in all_fs:
                pass
            else:
                # if it's a new ftheta, add it to the list
                all_fs.append(fs)
                self.valid_fthetas.append(t)

    def fill_template(self, templates, epsilon=False):
        """Iterates through templates, and creates any possible manipulation
        of each template with the current limits.

        Parameters
        ----------
        templates : ``list``
            The templates to be manipulated.
        epsilon : ``bool``
            True if the templates evalaute to zero.

        Returns
        -------
        template_subs : ``list``
            A list of templates filled by parameters approaching their limits.

        Example
        -------
        limits: {"p1": "inf", "p2": "inf"},

        template = "inf_1/inf_2",

        returns ["p1/p2", "p2/p1"]

        """
        # Uses one template to create all possible versions of that template
        # start with an empty set
        template_subs = set([])
        # cycle though all templates
        subs = self.find_limit_subs()
        for t in templates:
            for sub_list in subs:
                subbed = self.sub_params_in_template(sub_list, t, epsilon)
                # if the substitution was successful, add it to the set
                if subbed:
                    template_subs.add(subbed)
        return list(template_subs)

    def sub_label_name(self, subbed_eq, epsilon):
        """A simiple algorithm to rename new parameters.

        Parameters
        ----------
        subbed_eq : ``str``
            The parameter equation to be renamed
        epsilon : ``bool``
            Automatically renames parameter to 'epsilon' if True.

        Returns
        -------
        label : ``str``
            The new label for the parameter combination.

        Example
        -------
        a/b -> a_over_b
        """
        # assigns the new parameters names. Just subs out math operations for words.
        if epsilon:
            return "epsilon"
        else:
            label = str(subbed_eq).replace(" ", "")
            for rep in self.label_subs:
                label = label.replace(rep[0], rep[1])
            return label

    def add_to_ftheta(self, subbed, epsilon):
        """Once the templates are filled, fthetas need to be created.

        Parameters
        ----------
        subbed : ``SymPy`` symbolic equation
            The new parameter combination as an equation.
        epsilon : ``bool``
            True if the parameter combination evaluates to zero.
        """
        # adds item to dictionary where key(param_name) => potential ftheta
        for a in subbed.atoms():
            if str(a) in self.fthetas:
                temp = {"theta": str(a),
                        "limit": self.ls[str(a)],
                        "f": subbed,
                        "tilde": self.sub_label_name(subbed, epsilon)}
                # make sure the partial ftheta isn't already in the list of partial fthetas for that parameter
                if temp not in self.fthetas[str(a)]:
                    self.fthetas[str(a)].append(temp)

    def sub_params_in_template(self, sub_list, template, epsilon):
        """Replaces limit types in templates with actual parameters.

        Parameters
        ----------
        sub_list : ``list``
            List of SymPy substitutions of the form (limit_type, parameter).
        template : ``dict``
            Template dictionary to be substituted with parameters.
        epsilon : ``bool``
            True if the template evaluates to zero.
        """
        # replaces all the template variables with proper parameters
        # then adds the new values to the ftheta dictionary
        params = [str(s[1]) for s in sub_list]
        subbed_template = sympify(template['template']).subs(sub_list)
        all_replaced = (subbed_template.atoms() & sympify(template['template']).atoms())
        # if all the parameters in the template have been substituted
        if len(all_replaced - set([-1])) == 0:
            # try to add it to the partial ftheta dictionary
            self.add_to_ftheta(subbed_template, epsilon)
            return subbed_template
        # otherwise, return nothing
        return None

    def find_limit_subs(self):
        """Creates possible substitutions (template_name, param_name).

        If two parameters are approaching infinity then the potential names for
        those parameters could be either 'inf_1' or 'inf_2'. This function
        finds a list of all possible parameter limit namings.

        Returns
        -------
        template_fill_list : ``list``
            A list that contains all possible subs for the parameters to fill
            the limits.

        Example
        -------
        {"a": "inf"} => the template needs one infinity:

        returns [[('a', 'inf_1')], [(('b', 'inf_1)]]

        {"a": "inf", "b": "inf"}=> the template needs two infinities:

        returns [[('a', 'inf_1'), ('b', 'inf_2)], [('a', 'inf_2'), ('b', 'inf_1)]]
        """
        # takes in a list of parameters and their limit type
        # returns all possible tuples ('template_name', 'param_name')
        ret = []
        # create all ordered sets of some list ex: [p1, p2] => [(p1, p2), (p2, p1)]
        # this allows the limit template indecies to use every potential parameter
        for subset in itertools.permutations(self.ls.keys(), len(self.ls)):
            # keep track of the limit index for the parameter ex: zero_1, zero_2, etc.
            count = {}
            # store these in their own layer
            layer = []
            # for each element in the subset
            for i, s in enumerate(subset):
                # if this limit type has not been counted before
                if self.ls[s] not in count:
                    count[self.ls[s]] = 1
                else:
                    count[self.ls[s]] += 1
                # add a substitution with the [(limit_name)_(index), (parameter_name)]
                layer.append(tuple(("{0}_{1}".format(self.ls[s], count[self.ls[s]]), s)))
            # if this layer has not been added to the list, add it
            if set(layer) not in ret:
                ret.append(set(layer))
        # partition up the list to be a list of lists of tuples.
        # where each list of tuples represents one full parameter substitution
        # and each of those lists is placed inside a list of all potential full parameter substitutions
        return [list(x) for x in ret]

    def count_limits(self):
        """Creates a mapping to see how many of each limit is being reached
        by the parameters. This is used as the `limit_key` and will filter
        templates.
        """
        # create a dictionary mapping from limit_type => list of parameters at that limit
        # also, create a key for the current limit to compare with template keys
        self.sorted_ls = {}
        self.limit_key = [0 for k in self.limit_to_index]
        for param, limit in self.ls.items():
            self.limit_key[self.limit_to_index[limit]] += 1
            if limit not in self.sorted_ls:
                self.sorted_ls[limit] = [param]
            else:
                self.sorted_ls[limit].append(param)
        self.limit_key = tuple(self.limit_key)
