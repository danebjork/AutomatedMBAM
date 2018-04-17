"""
Manages the HDF5 files and reading of HDF5 byte strings from the UI. HDF5
file types are somewhat tricky to work with over websockets and cannot be
read using javascript, so this module contains some workarounds for that.
"""
import json
import os
import h5py
from .hdf5tojson import HDF5_JSON
from ..mongo import MMongo

class MData:
    def __init__(self):
        self.id = None
        self.mongo = MMongo()
        self.file_path = None
        self.data_json = None

    # def load_from_model_id(self, model_id):
    #     # Query mongo for the model
    #
    #     # Get the data id from the query
    #     # self.load_from_data_id(data_id)
    #     pass
    #
    # def load_from_model_name(self, model_id):
    #     # Query mongo for the model by name
    #     # Get the data id from the query
    #     # self.load_from_data_id(data_id)
    #     pass

    def load_from_id(self, data_id):
        """Loads the data from the database with the matching id. Saves it to
        an hdf5 file, and saves the id.

        Parameters
        ----------
        data_id : ``str``
            The id of the data object to be loaded.
        """
        self.id = data_id
        self.data_json = self.mongo.load_data_id(data_id)
        self.save_to_hdf5()

    def load_bytes(self, byte_str):
        """Saves the string of raw bytes to a file, then reads that file
        using the hdf5 library.

        Parameters
        ----------
        byte_str : ``byte_str``
            The hdf5 data in ``byte_str`` format.
        """
        #data = await ws.recv()
        # Save the bytes to a file
        with open(os.path.join(os.getcwd(), "temp.h5"), 'wb') as h:
            h.write(byte_str)
            h.close()
        self.load_hdf5(os.path.join(os.getcwd(), "temp.h5"))

    def save_data(self):
        """Saves the hdf5 data to the database.
        """
        self.save_to_hdf5()
        self.id = self.mongo.save_model_data(self.data_json)

    def create_zero_data(self, num_vars, t_start, t_end, t_step):
        """Creates data full of zeros with the given lengths, and saves the data
        to an hdf5 file.

        Parameters
        ----------
        num_vars : ``int``
            The number of variables being observed.
        t_start : ``float``
            The starting point for the time axis.
        t_end : ``float``
            The final point for the time axis.
        t_step : ``float``
            The step size taken for each time point.
        """
        # create the necessary numpy arrays
        t = np.arange(t_start, t_end, t_step)
        ydata = np.zeros((num_vars, t.shape[0]))
        weights = np.ones((num_vars, t.shape[0]))
        self.save_data()

    def load_hdf5(self, file_path):
        """Loads an hdf5 file.

        Parameters
        ----------
        file_path : ``str``
            The full path to the hdf5 file.
        """
        self.file_path = file_path
        # Use a hdf5 to json converter. Input is file location
        self.data_json = json.loads(HDF5_JSON(self.file_path).jsonString())
        self.save_data()

    def save_to_hdf5(self, full_path="temp.h5"):
        """Saves the data to an hdf5 file.

        Parameters
        ----------
        full_path : ``str``
            The path to where the file will be saved. Defaults to "./temp.h5".
        """
        if full_path == "temp.h5":
            self.file_path = os.path.join(os.getcwd(), "temp.h5")
        else:
            self.file_path = full_path
        if self.data_json:
            data_file = h5py.File(self.file_path, 'w')
            data_file.create_dataset('ydata', data=self.data_json['ydata'])
            data_file.create_dataset('weights', data=self.data_json['weights'])
            data_file.create_dataset('t', data=self.data_json['t'])
            data_file.close()
        else:
            print("DATA NOT LOADED OR CREATED!")
