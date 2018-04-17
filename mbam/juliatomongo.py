"""This module initializes a  `Collector` object. This object then runs
until it is manually killed, or until the geodesic that it is connected to
completes or crashes. It forwards all the data from the geodesic on to
MongoDB.

This module is started at the same the Julia Geodesic script is started. Once
a stable package for Julia is released connecting to MongoDB, this class
should be removed and the geodesic should report directly to MongoDB. However,
it seems that is not currently an option.
"""

import time
import zmq
from .mongo import *

class Collector:
    """Uses ZMQ sockets to connect to the Julia Geodesic currently running,
    forwards the data collected to MongoDB.
    """
    def __init__(self, geo_id):
        """
        Parameters
        ----------
        geo_id : ``str``
            The MongoDB ObjectID as a string, corresponding to the current
            geodesic.
        """
        self.mongo = MbamMongo()
        self.geo_id = geo_id
        self.start_sockets()
        self.collect()

    def start_sockets(self):
        """Intializes the ZMQ socket on port 5556.
        """
        context = zmq.Context()
        self.rec = context.socket(zmq.PULL)
        self.rec.bind("tcp://127.0.0.1:5556")

    def collect(self):
        """Collects the data from the Julia Geodesic running.

        Will run until the process is killed manually, or until the
        Geodesic reports that the script has either completed or crashed.
        """
        total = 0
        while True:
            data = self.rec.recv_json()
            total += 1
            if 'done' in data:
                self.mongo.finish_geodesic(self.geo_id, exception=True)
                break
            else:
                self.mongo.push_geodesic(self.geo_id, data)
        self.rec.close()


if __name__ == "__main__":
    import sys
    Collector(sys.argv[1])
