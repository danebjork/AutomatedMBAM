"""
A module for communication between the user interface websocket handler
and MBAM functionality. This class takes the place of MBAM Engine when using
the UI. It is not made to be used outside of use with the UI.
"""
import json
from .modeling import *
from .parsing import *
from .iteration import Iteration
from .mongo import MMongo
import numpy as np
from sympy import gruntz, Symbol, sympify, simplify
import logging

class MbamUI:
    def __init__(self):
        self.logger = logging.getLogger("MBAM.UI")
        self.logger.debug("Initialzing MBAMUI")
        self.model = None
        self.mongo = MMongo()
        self.model_id = None
        self.iter = None
        self.data = MData()

    def save_model(self, model_dict, options):
        """Saves a model dictionary to the database and creates a model object.

        Parameters
        ----------
        model_dict : ``dict``
            A dictionary containing all necessary information for a model.

        Returns
        -------
        ``dict``
            A dictionary containing model info to be sent to the UI.
        """
        self.logger.debug("Saving model with options = %s" %options)
        # save the model dictionary as a model
        self.save_model_dict(model_dict)
        # save the model into the database with the data id

        # Update data_id if not existing~~
        self.model_id = self.mongo.save_model(self.model, self.data.id)
        self.logger.info("Saved model: %s" %self.model_id)
        self.begin_iteration()
        self.iter.write_model_script(options) # Options should probably be saved in the database with the rest of the model
        return self.send_save_done()

    def save_model_dict(self, model_dict):
        """Turns a model dictionary into an MbamModel object.

        Parameters
        ----------
        model_dict : ``dict``
            A dictionary containing all necessary information for a model.
        """
        if model_dict['type'].lower() == "ode":
            self.model = ODE(model_dict)
        elif model_dict['type'].lower() == "dae":
            self.model = DAE(model_dict)

    def load_model_id(self, id_str):
        """Use a model id to load the model and its data. Send necessary
        information forward to the user interface.

        Parameters
        ----------
        id_str : ``str``
            A string representing a model id.

        Returns
        -------
        ``dict``
            A dictionary containing a model and its data, if data is associated
            with the given model.
        """
        # try:
        data = self.mongo.load_model_id(id_str)
        self.model_id = id_str
        print("MODEL LOADED", data['model']['data_id'])
        if data['model']['data_id'] != "None":
            self.data.load_from_id(data['model']['data_id'])
        self.save_model_dict(data['model'])
        self.begin_iteration()
        return data
        # except:
        #     self.model_id = None
        #     return {}

    def iterate_model(self):
        """Updates the model and id to the N-1 model and N-1 model id, then
        creates a new mbam iteration object.
        """
        self.model_id = self.iter.N_minus_1_id
        self.model = self.iter.N_minus_1
        self.begin_iteration()

    def read_model_data(self, data_str):
        """Takes in hdf5 byte string from the websocket, saves it to a temp.h5
        file to be loaded in the Julia scripts.

        Parameters
        ----------
        data_str : ``byte_str``
            A raw string of bytes representing all hdf5 data contained in a file.
        """
        self.data.load_bytes(data_str)
        self.begin_iteration()

    def send_model_load_done(self):
        """
        Returns
        -------
        ``dict``
            Response to be send to the UI containing a model dict.
        """
        to_send ={
            "type": "load-model",
            "model": self.model.str_dict,
        }
        return json.dumps(to_send)

    def send_save_done(self):
        """
        Returns
        -------
        ``dict``
            Response to be send to the UI containing a model dict and a model
            in latex formatting.
        """
        to_send = {
            "type": "post-save",
            "latex": self.model.latex_eqs,
            "md": self.model.str_dict,
        }
        return json.dumps(to_send)

    def send_data_done(self):
        """
        Returns
        -------
        ``dict``
            Response to be send to the UI containing the data read in the hdf5 file.
        """
        to_send = {
            "type": "model-data",
            "data": {
                "t": self.data.data_json['t'],
                "ydata": self.data.data_json['ydata'],
                "weights": self.data.data_json['weights'],
            }
        }
        return json.dumps(to_send)

    def scripts_ready(self):
        """Checks if an iteration has been made. If it has been made, then the
        julia scripts will be ready to be sent.

        Returns
        -------
        ``bool``
            True if the scripts are ready to be sent.
        """
        return bool(self.iter)

    def send_scripts(self):
        """
        Returns
        -------
        ``dict``
            Response to be send to the UI containing the julia model and geodesic scripts.
        """
        to_send = {
            "type": "julia-scripts",
            "model": self.iter.julia.script,
            "geo": self.iter.geo_parser.script,
        }
        return json.dumps(to_send)

    def begin_iteration(self):
        """Checks if a model and its data have been saved, if so, an mbam iteration
        will be created.
        """
        if self.model_id and self.data.id:
            self.iter = Iteration(self.model, self.model_id, self.data.file_path)

    def update_julia_options(self, options):
        """Update the julia model options and send the new generated scripts
        to the UI.

        Parameters
        ----------
        options : ``dict``
            Julia model options.

        Returns
        -------
        ``dict``
            A dictionary containing the new script to be sent to the UI.
        """
        self.iter.add_julia_options(options)
        # options updated in database too...
        return self.send_scripts()

    def update_geo_options(self, options):
        """Update the julia geodesic options and send the new generated scripts
        to the UI.

        Parameters
        ----------
        options : ``dict``
            Julia geodesic options.

        Returns
        -------
        ``dict``
            A dictionary containing the new script to be sent to the UI.
        """
        self.iter.add_geo_options(options)
        # options updated in database too...
        return self.send_scripts()

    def update_julia_script(self, script):
        """Update the julia model script sent from the UI.

        Parameters
        ----------
        options : ``str``
            Julia model script.
        """
        self.iter.update_julia_script(script)
        # update script in iter, update script in db

    def update_geo_script(self, script):
        """Update the julia geodesic script sent from the UI.

        Parameters
        ----------
        options : ``str``
            Julia geodesic script.
        """
        self.iter.update_geo_script(script)
        pass # update script in iter, update script in db

    def start_geodesic(self):
        """Start the subprocesses necessary for the geodesic to run.
        """
        self.iter.init_geodesic()
        self.iter.geodesic.start()

    def kill_geodesic(self):
        """Kill the subprocesses used to run the geodesic.
        """
        self.iter.geodesic.kill()

    def query_geo(self):
        """Get the geodesic data and get it ready to be sent to the UI.

        Returns
        -------
        ``dict``
            The geodesic data to be sent to the UI.
        """
        return json.dumps(self.iter.geodesic.curr_data())

    def simplify_eq(self, eq):
        """Takes an equation from the UI, simiplifies it, and sends the
        simplified version back to the UI.

        Parameters
        ----------
        eq : ``str``
            The equation to be simplified.

        Returns
        -------
        ``dict``
            A dictionary containing the equation as both a string and latex string.
        """
        simp_eq = simplify(sympify(eq))
        to_send = {
            "type": "simplify",
            "eq": str(simp_eq),
            "latex": latex(simp_eq)
        }
        return json.dumps(to_send)

    def eval_epsilon(self, eq):
        """Evaluates the limit as epsilon goes to zero in the given equation.

        Parameters
        ----------
        eq : ``str``
            The equation to be evaluated.

        Returns
        -------
        ``dict``
            The dictionary containing the equation evaluated as epsilon goes to zero.
        """
        eps = gruntz(simplify(sympify(eq)), Symbol("epsilon"), 0)
        to_send = {
            'type': "epsilon",
            'eq': str(eps),
            'latex': latex(eps)
        }
        return json.dumps(to_send)

    def sub_ftildes(self, eq):
        """Substitutes f_inv in for the old parameters in the given equation.

        Parameters
        ----------
        eq : ``str``
            The equation with parameters to be substituted.

        Returns
        -------
        ``dict``
            Contains the newly substituted equation as a string and latex string.
        """
        eq = sympify(eq).subs(self.iter.ftilde_subs)
        send = {
            'type': 'substitute',
            'eq': str(eq),
            'latex': latex(eq)
            }
        return json.dumps(send)

    def load_ftheta(self, fthetas):
        """Takes the fthetas from the UI, transforms them to ftildes, creates
        the substitutes for those ftildes, and applies those substitutions to
        the model.

        Parameters
        ----------
        fthetas : ``list``
            A list of ftheta dictionaries.

        Returns
        -------
        ``bool``
            True if the reparameterization with ftilde is successful.
        """
        self.iter.solve_ftildes(fthetas)
        if len(self.iter.ftildes) == 0:
            return False
        self.iter.create_tilde_subs(self.iter.ftildes)
        return self.iter.apply_ftilde()

    def manual_iterate(self, model_dict):
        """Used when the user updates the model manually.

        Recieves a new model, checks if the model is valid, then completes
        the iteration from N to N-1.

        Parameters
        ----------
        model_dict : ``dict``
            The dictionary representing the N-1 model.

        Returns
        -------
        ``dict``
            The new model dictionary to have the UI update with it as the N model.
        """
        if model_dict['type'].lower() == "ode":
            model = ODE(model_dict)
        elif model_dict['type'].lower() == "dae":
            model = DAE(model_dict)
        if model.is_valid():
            self.model = model
            self.model_id = self.mongo.save_model(self.model, self.data.id)
            self.begin_iteration()
            to_send = {
                "type": "load-model",
                "model": self.model.str_dict,
                }
            return json.dumps(to_send)
        else:
            print("INVALID MODEL")

    def iterate(self):
        """Saves and updates the N-1 model to the N model.

        Returns
        -------
        ``dict``
            The dictionary containing the N-1 model to be udpated as the N model
            in the UI.
        """
        self.iter.save_iteration()
        self.iterate_model()
        to_send = {
            "type": "load-model",
            "model": self.model.str_dict,
            }
        return json.dumps(to_send)
