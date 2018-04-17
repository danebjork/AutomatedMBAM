"""
A custom client for connecting to MongoDB and managing the data flow
for MBAM. Six collections are used in the database 'mbam':

geos: geodesic storage.
models: model storage.
model_data: the data read in the hdf5 files. Used in models.
iters: successful MBAM iteration storage.
temp_key: the key for navigating limit templates.
temps: limit template storage.
"""
from pymongo import MongoClient
from bson.objectid import ObjectId

class MMongo:
    def __init__(self):
        """Starts the client, connects to the 'mbam' database and creates
        shortcuts to the collections.
        """
        client = MongoClient()
        self.db = client['mbam']
        self.geo = self.db['geos']
        self.models = self.db['models']
        self.data = self.db['model_data']
        self.iters = self.db['iters']
        self.temp_key = self.db['temp_key']
        self.temps = self.db['temps']

    def update_temp_key(self, key):
        """ Overwrites the current template key with the given `key`.

        Parameters
        ----------
        key : ``dict``
            A dictionary of the format: {"limit_type": "index in key"}

        Example
        -------
        key = {"zero": 0, "inf": 1}
        """
        if self.temp_key.find({}).count() == 0:
            self.temp_key.insert_one(key)
        else:
            self.temp_key.find_one_and_replace({}, key)

    def get_temp_key(self):
        """

        Returns
        -------
        key : ``dict``
            A dictionary of the format: {"limit_type": "index in key"}
        Example
        -------
        key = {"zero": 0, "inf": 1}
        """
        return self.temp_key.find_one({}, {"_id":0})

    def save_temp(self, temp):
        """Saves a single template in the database.

        Parameters
        ----------
        temp : ``dict``
            A template dictionary.

        Example
        -------
        template = {'key': [0, 1], 'template': '1/inf_1', 'label': 'epsilon',
        'class': 'michaelis-menten' }
        """
        test = {
            "key": temp["key"],
            "template": temp["template"],
            "class": temp["class"]
            }
        if self.temps.find(test).count() == 0:
            self.temps.insert_one(temp)

    def save_temps(self, temp_list):
        """Saves a list of templates in the database.

        Parameters
        ----------
        temp : ``list``
            A list of template dictionaries.

        Example
        -------
        temp_list = [{'key': [0, 1], 'template': '1/inf_1', 'label': 'epsilon',
            'class': 'michaelis-menten' }]
        """
        # use key to see if already in collection
        # if it is, update the list
        # otherwise, add it to the collection
        for t in temp_list:
            self.save_temp(t)
        # self.temps.insert_many(temp_list)

    def load_templates(self, key=None, clss=None):
        """Loads all limit templates and filters them by `key` and `clss`.

        Parameters
        ----------
        key :  ``list`` or ``tuple`` of ``int``
            A list or tuple of ints defining how many of each limit type
            occurs within a template.
        clss : ``str``
            A string used to define the model class that is going to use
            the templates.

        Returns
        -------
        list : ``list``
            A list of dictionary templates after filtering by key and class.

        Example
        -------
        Model classes are user defined, just be consistent.
        """
        to_ret = {
            "eps": [],
            "finite": [],
        }
        if clss:
            curr = self.temps.find({"class": clss}, { '_id': 0})
        else:
            curr = self.temps.find({}, { '_id': 0})
        if curr.count() == 0:
            curr = self.temps.find({}, { '_id': 0})
        for c in curr:
            if self.temp_key_filter(key, c['key']):
                if c['label'] == "epsilon":
                    to_ret['eps'].append(c)
                else:
                    to_ret['finite'].append(c)
        # print("TEMPLATES", to_ret)
        return to_ret

    def temp_key_filter(self, curr_key, temp_key):
        """Returns true if `curr_key[i]` < `temp_key[i]` for all i.

        Parameters
        ----------
        curr_key :  ``list`` or ``tuple`` of ``int``
            A list or tuple of ints defining how many of each limit type
            occurs within the current limit.
        temp_key :  ``list`` or ``tuple`` of ``int``
            A list or tuple of ints defining how many of each limit type
            occurs within a queried template.

        Returns
        -------
        valid : ``bool``
            True if the queried template is functional with the current limit.
        """
        if not curr_key:
            return True
        elif len(curr_key) < len(temp_key):
            print("temp_key needs updating!\n NO FILTER APPLIED!")
            return True
        else:
            for i, val in enumerate(curr_key):
                if val < temp_key[i]:
                    return False
        return True

    def query_geodesic(self, geo_id):
        """

        Parameters
        ----------
        geo_id : ``str``
            The ID for the geodesic to query.

        Returns
        -------
        geo_data : ``dict``
            The data queried from the current geodesic, excluding its ID.
        """
        return self.geo.find_one({"_id": ObjectId(geo_id)}, {"_id":0})

    def push_geodesic(self, geo_id, data):
        """Append new geodesic data to the end of the current geodesic data.

        Parameters
        ----------
        geo_id : ``str``
            The ID for the geodesic to add the data to.
        data : ``dict``
            The dictionary of new data to be appended to the current geodesic.
        """
        push = {
            "t": data["t"][0],
            "tau": data["tau"][0],
            "v": data["v"],
            "x": data["x"],
            # "j": data["j"],
        }
        self.geo.update_one({"_id": ObjectId(geo_id)}, {"$push": push})

    def init_geodesic(self):
        """Creates a new geodesic object inside MongoDB.

        Returns
        -------
        geo_id : ``str``
            The string representation of the new geodesic.
        """
        post = {
            # "name": self.model_name,
            "t": [],
            "tau": [],
            "v": [],
            "x": [],
            # "j": [],
        }
        return str(self.geo.insert_one(post).inserted_id)

    def finish_geodesic(self, geo_id, exception=False):
        """Marks the geodesic as 'done' inside MongoDB.

        This allows the object waiting for the geodesic to finish to know
        it has completed.
        """
        if exception:
            done = "excpetion"
        else:
            done = "done"
        self.geo.update_one({"_id":ObjectId(geo_id)}, {"$set": {"done": done}})

    def get_hasse_children(self, model_id):
        """Returns the length of a model's successful iterations.

        Is used to create a unique name for several models with the same parent
        model.

        Parameters
        ----------
        model_id : ``str``
            The id for the parent model.

        Returns
        -------
        len_to_iter : ``int``
            The total number of children the parent model already has.
        """
        return len(self.models.find_one({"_id": ObjectId(model_id)})['to_iter'])

    def push_model_to_iter(self, model_id, iter_id):
        """Add the successful iteration id to the parent model.

        Parameters
        ----------
        model_id : ``str``
            The id for the parent model.
        iter_id : ``str``
            The id for the successful iteration.
        """
        self.models.find_one_and_update({"_id": ObjectId(model_id)}, {"$addToSet": {"to_iter": iter_id}})

    def push_model_from_iter(self, model_id, iter_id):
        """Add the successful iteration id to the child model.

        Parameters
        ----------
        model_id : ``str``
            The id for the child model.
        iter_id : ``str``
            The id for the successful iteration.
        """
        self.models.find_one_and_update({"_id": ObjectId(model_id)}, {"$addToSet": {"from_iter": iter_id}})

    def save_iteration(self, iteration):
        """Add the successful iteration to the database.

        Parameters
        ----------
        iteration : ``dict``
            All data corresponding to the iteration.

        Returns
        -------
        iter_id : ``str``
            The id generated by MongoDB. Used to udpate parent/child models.
        """
        return str(self.iters.insert_one(iteration).inserted_id)

    def save_model(self, mbam_model, data_id=None):
        """

        Parameters
        ----------
        mbam_model : ``mbammodel``
            The model object to be saved.
        data_id : ``str``
            The id of the saved data in the database. Used to connect the model
            to its data.
        """
        # write model to db
        to_save = mbam_model.str_dict
        to_save['to_iter'] = []
        to_save['from_iter'] = []
        to_save['data_id'] = data_id
        return str(self.models.insert_one(to_save).inserted_id)

    def save_model_data(self, data_json):
        """
        Parameters
        ----------
        data_json : ``dict``
            The HDF5 data to be saved inside the database.

        Returns
        -------
        data_id : ``str``
            The id generated by MongoDB while saving the data.
        """
        return str(self.data.insert_one(data_json).inserted_id)

    # def load_model(self, model_name):
    #     """
    #     """
    #     # return  model_dict with corresponding name
    #     pass

    def load_model_id(self, model_id_str):
        """Retrieves a model from the database with the given id.

        Parameters
        ----------
        model_id_str : ``str``
            The model id to query.

        Returns
        -------
        model_dict : ``dict``
            The model and data (if exists) connected to the given id.
        """
        to_ret = {}
        filter = {"_id":0, "to_iter": 0, "from_iter": 0}
        to_ret["model"] = self.models.find_one({"_id": ObjectId(model_id_str)}, filter)
        to_ret["model"]["data_id"] = str(to_ret["model"]["data_id"])
        data_id = to_ret["model"]["data_id"]
        if data_id != "None":
            to_ret["data"] = self.load_data_id(data_id)
        return to_ret

    def load_data_id(self, data_id_str):
        """
        Parameters
        ----------
        data_id_str : ``str``
            The id for the data object to find.

        Returns
        -------
        data : ``dict``
            The dictionary containing all the data found in the database.
        """
        data = self.data.find_one({"_id": ObjectId(data_id_str)}, {"_id": 0})
        return data
