"""
This class manages everything necessary to go from a model with N parameter to
a model with N-1 parameters. This includes running the geodesic, inferring
the limits, reparameterizing the model, as well as evaluating singular perturbations.
"""

from .modeling import *
from .parsing import *
from .mongo import MMongo
from .limits import *
from .geodesic import Geodesic
# from singular_limit import SingularLimit
from copy import deepcopy
# from reparameterize import Reparams
from sympy import sympify, solveset
import os

class Iteration:
    def __init__(self, model, model_id, data_path):
        """
        Parameters
        ----------
        model : ``mbammodel``
            Either Function, ODE, or DAE.
        model_id : ``str``
            The id of the model with N parameters.
        data_path : ``str``
            The full path to the hdf5 data file for the model.
        """
        self.N = model
        self.N_id = str(model_id)
        self.mongo = MMongo()
        self.data_path = data_path
        self.N_minus_1 = None
        self.N_minus_1_id = None
        self.ftildes = None
        self.geo_id = None
        self.init_parsers()

    def init_geodesic(self):
        """Creates the Geodesic object, and retrieves its id.
        """
        self.geodesic = Geodesic(self.geo_parser, os.path.join(os.getcwd(), 'juliatomongo.py'))
        self.geo_id = self.geodesic.geo_id

    def find_limits(self):
        """Starts the geodesic and runs until a limit is found, or until the
        geodesic crashes.
        """
        self.init_geodesic()
        return self.limit_keys_to_ps(self.geodesic.run_geo_auto())

    def kill_geodesic(self):
        """Kills the geodesic subprocess.
        """
        self.geodesic.kill()

    def limit_keys_to_ps(self, limits):
        """Converts what the geodesic returns to a more useable format.

        Parameters
        ----------
        limits : ``dict``
            A dictionary of limits returned by the geodesic.

        Returns
        -------
        limits : ``dict``
            A dictionary of limits converted to new format.

        Example
        -------
        Converts (p_index: limit) to (p_name: limit).
        """
        # Geodesic returns {"1": "Inf"} where "1" is the index of the parameter
        # The Reparameterization needs limits of the form {"p1": "inf"} where the key is the param name
        self.limits = {}
        for key, lim in limits.items():
            self.limits[self.N.model_ps.non_constants[int(key)]] = lim
        return self.limits

    def init_parsers(self):
        """Assigns the parser for the model based off the model type, then it
        creates the geodesic parser.
        """
        if self.N.type == "function":
            self.julia = FunctionParser(self.N, self.data_path)
        elif self.N.type == "ode":
            self.julia = ODEParser(self.N, self.data_path)
        elif self.N.type == "dae":
            self.julia = DAEParser(self.N, self.data_path)
        self.geo_parser = GeodesicParser(self.N, self.julia.file_path, os.path.join(os.getcwd(),"geosender.jl"))

    def add_julia_options(self, options):
        """Update the options for the Julia model parser.

        Parameters
        ----------
        options : ``dict``
            options = {"bare": ``bool``, "weights" ``bool``}
        """
        # update database for julia options
        self.julia.update_options(options)

    def add_geo_options(self, options):
        """Update the options for the Julia geodesic parser.

        Parameters
        ----------
        options : ``dict``
            options = {

                "tmax": ``float``,

                "lambda": ``float``,

                "abstol": ``float``,

                "reltol": ``float``,

                "use_svd": ``bool``,

                "use_pinv": ``bool``,
                
            }

        """
        self.geo_parser.update_options(options)

    def update_julia_script(self, script):
        """Overwrite the current julia model script.

        Parameters
        ----------
        script : ``str``
            The Julia Model file as a string.
        """
        # update database for julia options
        self.julia.save_to_file(script)

    def update_geo_script(self, script):
        """Overwrite the current julia geodesic script.

        Parameters
        ----------
        script : ``str``
            The Julia geodesic file as a string.
        """
        self.geo_parser.save_to_file(script)
        # update in database

    def auto_run(self):
        """Finds the limits, applies the limits, and saves the new model if successful.

        Returns
        -------
        ``bool``
            True if the iteration was successful and saved.
        """
        print("RUNNING GEODESIC")
        self.find_limits()
        print("LIMITS FOUND: ", self.limits)
        if self.apply_limits(self.limits):
            print("SUCCESSFUL EVALUATION!")
            self.save_iteration()
            return True
        else:
            print("EXCEPTIONS NEEDED")
            return False

    def save_iteration(self):
        """Adds the iteration to the database, updates the parent and child
        models with the successful iteration id.
        """
        self.N_minus_1.update_name(self.mongo.get_hasse_children(self.N_id))
        self.N_minus_1_id = self.mongo.save_model(self.N_minus_1)
        self.id = self.mongo.save_iteration(self.dict)
        print("SAVING N-1 TO MONGO")
        self.mongo.push_model_to_iter(self.N_id, self.id)
        self.mongo.push_model_from_iter(self.N_minus_1_id, self.id)

    @property
    def dict(self):
        """``dict``: Turn the iteration into a dictionary for saving."""
        str_ftildes = []
        for f in self.ftildes:
            new_f = {}
            for key, val in f.items():
                new_f[key] = str(val)
            str_ftildes.append(new_f)

        to_ret = {
            "from_model": self.N_id,
            "to_model": self.N_minus_1_id,
            "geo": self.geo_id,
            "ftildes": str_ftildes,
            }
        return to_ret

    def apply_limits(self, limits):
        """Attempts to reparameterize the model. If not successful, exceptions
        are attempted with Singular Perturbations.

        Parameters
        ----------
        limits : ``dict``
            Dictionary of limits to be applied to the model.

        Returns
        -------
        ``bool``
            True if the limits were applied successfully.
        """
        print("APPLYING")
        rep = Reparam(limits, self.mongo.get_temp_key())
        temps = self.mongo.load_templates(rep.limit_key, self.N.clss)
        fthetas = rep.get_fthetas(temps['eps'], temps['finite'])
        for ftheta in fthetas:
            # create ftildes
            self.solve_ftildes(ftheta)
            if len(self.ftildes) == 0:
                return False
            self.create_tilde_subs(self.ftildes)
            # create ftide subs
            # print(self.ftildes)
            if self.apply_ftilde():
                return True
        # if nothing is successful, don't save the ftildes
        self.ftildes = None
        return False

    def apply_ftilde(self, exception=False):
        """Attempts to evaluate epsilon approaching zero. If the model is valid,
        it returns True. If it is not valid, the function is called again and
        attempts singular perturbation before evaluating the limit.

        Parameters
        ----------
        exception : ``bool``
            True if reparameterization has failed without an exception applied.

        Returns
        -------
        ``bool``
            True if the evaluation was successful.
        """
        print(self.ftildes, "\n")
        self.N_minus_1 = deepcopy(self.N)
        self.N_minus_1.substitute(self.ftilde_subs)
        # print("TILDE", self.ftildes)
        self.update_params(self.ftildes)
        if exception:
            print("TRYING SINGULAR LIMIT")
            self.try_singular_limit()
        else:
            self.N_minus_1.eval_epsilon()
        realized = self.realize_limit()
        if realized:
            print("REALIZED")
            self.parse_templates()
            return True
        elif not realized and not exception:
            if self.apply_ftilde(exception=True):
                return True
        return False

    def parse_templates(self):
        """If the iteration is successsful, the ftildes are parsed into
        templates to be saved in the database.

        Example
        -------
        ftilde = {"theta": "p1", "limit": "inf", "tilde": "epsilon", "f": "1/p1", "f_inv": "1/epsilon"}
        """
        subs = []
        limit_count = {}
        for l in self.ftildes:
            if l['limit'] in limit_count:
                limit_count[l['limit']] += 1
            else:
                limit_count[l['limit']] = 1
            subs.append((sympify(l['theta']), sympify(l['limit']+"_"+str(limit_count[l['limit']]))))
        main_key = self.mongo.get_temp_key()
        for l in self.ftildes:
            temp = {
                "key":[],
                "template": None,
                "label": None,
                "class": self.N.clss
                }
            temp_f = sympify(l['f']).subs(subs)
            temp_key = [0 for k in main_key]
            for key in main_key:
                count = 0
                for a in temp_f.atoms():
                    if key in str(a):
                        count += 1
                temp_key[main_key[key]] = count
            temp["key"] = temp_key
            temp["template"] = str(temp_f)
            temp_label = str(l['tilde'])
            for s in subs:
                temp_label = temp_label.replace(str(s[0]), str(s[1]))
            temp['label'] = str(temp_label)
            self.mongo.save_temp(temp)

    def try_singular_limit(self):
        """Converts an ODE to a DAE, then attempts combinging equations to
        solve the singular perturbation error.
        """
        if self.N_minus_1.type == "ode":
#             self.update_params(self.ftildes)
            self.N_minus_1 = self.N_minus_1.to_dae()
        SingularLimit(self.N_minus_1)

    def realize_limit(self):
        """Checks if the model has been successfully applied.

        Returns
        -------
        ``bool``
            True if the new N-1 model is valid.
        """
        if self.N_minus_1.is_valid():
            print("VALID!")
            self.N_minus_1.check_subs()
            return True
        else:
            print("PARAMS", self.N_minus_1.all_params_in_eqs)
            print("FINITE", self.N_minus_1.check_eqs_finite)
            print("FAIL")
        return False

    def update_params(self, ftildes):
        """Uses ftilde to change the parameter names from those currently in the
        model to those found in the ftildes.
        """
        old = []
        new = []
        for tilde in ftildes:
            old.append(str(tilde['theta']))
            new.append(str(tilde['tilde']))
        self.N_minus_1.update_params(old, new)

    ###### TILDES #######
    def check_ftildes(self, solved):
        """Make sure that f_inv functions in ftilde don't contain any of
        the parameters to be removed from the old model.

        Parameters
        ----------
        solved : ``list``
            A list of ftildes.

        Returns
        -------
        ``bool``
            True if the f_inv doesn't contain any parameters to be removed.
        """
        thetas = set([])
        f_inv_atoms = set([])
        for s in solved:
            thetas = thetas | s['theta'].atoms()
            f_inv_atoms = f_inv_atoms | s['f_inv'].atoms()
        if len(thetas & f_inv_atoms) > 0:
            return False
        else:
            return True

    def solve_ftildes(self, ftheta):
        """Using ftheta, solve for f_inv to substitute in place of the old
        parameters.

        Parameters
        ----------
        ftheta : ``list``
            A list of fthetas to be solved.

        Returns
        -------
        ``list``
            A list of solved fthetas, now known as ftildes.

        Example
        -------
        ftheta = {"theta": "p1", "limit": "inf", "tilde": "epsilon", "f": "1/p1"}

        ftilde = {"theta": "p1", "limit": "inf", "tilde": "epsilon", "f": "1/p1", "f_inv": "1/epsilon"}
        """
        self.ftildes = []
        for f in ftheta:
            tilde = sympify(f['tilde'])
            theta = sympify(f['theta'])
            sym_eq = sympify(f['f']) - tilde
            solved = solveset(sym_eq, theta)
            solved_ftheta = {"theta": theta, "tilde": tilde, "limit": f['limit'], 'f':f['f']}
            try:
                if len(solved.args) > 1:
                    solved = solved.args[0].args[0]
                else:
                    solved = solved.args[0]
            except:
                print("INVALID THETA SUBSTITUTIONS")
                return []
            solved_ftheta['f_inv'] = solved
            self.ftildes.append(solved_ftheta)
            self.ftildes = self.unresolved_thetas(self.ftildes)
        return self.ftildes


    def unresolved_thetas(self, ftildes):
        """Substitutes out the old parameters in ftilde until no old paramters
        remain.

        Parameters
        ----------
        ftildes: ``list``
            A list of ftildes to be solved.

        Returns
        -------
        ``list``
            A list of solved ftildes, containing no old parameters

        Example
        -------
        ftilde1 = {"theta": "p1", "limit": "inf", "tilde": "epsilon", "f": "1/p1",  "f_inv": "1/epsilon"}

        old_ftilde2 = {"theta": "p2", "limit": "inf", "tilde": "p1_over_p2", "f": "p1/p2",  "f_inv": "p1/p1_over_p2"}

        old_ftilde2 still contains an old paramter: p1.

        new_ftilde2 = {"theta": "p2", "limit": "inf", "tilde": "p1_over_p2", "f": "p1/p2", "f_inv": "1/(epsilon*p1_over_p2"}
        """
        while not self.check_ftildes(ftildes):
            subs = self.create_tilde_subs(ftildes)
            for f in ftildes:
                f['f_inv'] = f['f_inv'].subs(subs)
        return ftildes

    def create_tilde_subs(self, ftildes):
        """Using ftildes, create a list of tuples for SymPy substitutions.

        Parameters
        ----------
        ftildes : ``list``
            A list of ftildes ready to be used for substitutions.

        Returns
        -------
        ``list``
            A list of SymPy substitutions.
        """
        # can also be used to substitute into the model
        self.ftilde_subs = []
        for f in ftildes:
            self.ftilde_subs.append((f['theta'], f['f_inv']))
        return self.ftilde_subs
