"""
A manager module for running and reporting on the geodesic.
"""

import subprocess
import time
import sys
import os
import numpy as np
from .mongo import MMongo

class Geodesic:
    def __init__(self, geo_parser, sender_file_path):
        """
        Parameters
        ----------
        geo_parser : ``parsing.geo``
            The parser object for the geodesic.
        sender_file_path : ``str``
            Path to the juliatomongo.py script. Run to connect to the Julia script
            and forward the data to MongoDB.
        """
        self.path = geo_parser.file_path
        self.data_sender = sender_file_path
        self.mongo = MMongo()
        self.limit_seq = []
        self.geo_id = self.mongo.init_geodesic()

    def run_geo_auto(self):
        """Runs the geodesic until manually killed, or until the limits are found.

        Returns
        -------
        limits : ``dict``
            A dictionary of limits. e.g. {"p1": "inf", "p2", "zero"}
        """
        self.start()
        self.limits = []
        try:
            while len(self.limits) == 0:
                self.limits = self.check_engine_geo(self.mongo.query_geodesic(self.geo_id))
                time.sleep(.4)
        finally:
            self.kill()
        return self.limits

    def kill(self):
        """Kills the subprocesses used to run the geodesic and the data collector.
        """
        self.data_collect_run.kill()
        self.geo_run.kill()

    def start(self):
        """Starts both subprocesses: the Julia geodesic and data collector.
        """
        self.data_collect_run = subprocess.Popen([sys.executable, self.data_sender, str(self.geo_id)])
        self.geo_run = subprocess.Popen(['julia', self.path])

    # def check_geo(self):
    #     """Queries the geodesic
    #     """
    #     data = self.curr_data()
        # data = self.mongo.query_geodesic(self.geo_id)

    def curr_data(self):
        """Queries the geodesic from the database and checks potential limits

        Returns
        -------
        ``dict``
            Contains geodesic data and any inferred limits.
        """
        data = self.mongo.query_geodesic(self.geo_id)
        data["x"] = np.array(data["x"]).transpose().tolist()
        return self.update_limits(data)

    def update_limits(self, geo_data):
        """Checks the current data for any potential limits used for UI.

        Parameters
        ----------
        geo_data : ``dict``
            The dictionary of geodesic data.

        Returns
        -------
        ``dict``
            The geodesic data and any limits inferred.
        """
        if "done" in geo_data and len(self.limit_seq) == 0:
            print("BAD CRASH")
            geo_data['limits'] = {}
            geo_data['type'] = "geo-done"
        elif "done" in geo_data and len(self.limit_seq) > 0:
            # print("BAD CRASH")
            geo_data['limits'] = self.limit_seq[-1]
            geo_data['type'] = "geo-done"
        elif len(geo_data["v"]) > 0:
            self.check_limits(geo_data["v"][-1])
            if len(self.limit_seq) > 6:
                geo_data['limits'] = self.limit_seq[-1]
                geo_data['type'] = "geo-done"
            else:
                geo_data['type'] = "geo"
        return geo_data

    def check_engine_geo(self, geo_data):
        """Checks the current data for any potential limits used for engine.
        """
        # engine geo cuts off automatically
        geo_data["x"] = np.array(geo_data["x"]).transpose().tolist()
        if "done" in geo_data and len(self.limit_seq) == 0:
            print("NO LIMIT REACHED IN GEODESIC")
            # Delete Failed Geodesic from database?
            return ["EMPTY"]
        elif "done" in geo_data and len(self.limit_seq) > 0:
            return self.limit_seq[-1]
        elif len(geo_data["v"]) > 0:
            self.check_limits(geo_data["v"][-1])
            if len(self.limit_seq) > 6:
                return self.limit_seq[-1]
        return []

    def check_limits(self, recent_vs):
        """Checks parameter velocities for any potential limits.

        Parameters
        ----------
        recent_vs : ``list``
            A list of the most recent parameter velocities.
        """
        limits = {}
        correctDir = 1
        vs = np.array(recent_vs)
        n = -1
        arglist = list(np.argsort(np.abs(vs)))
        arglist.reverse()
        if len(arglist) == 1:
            if np.abs(vs[arglist[0]]) > .9:
                n = 1
        else:
            for i, item in enumerate(arglist):
                if i != len(arglist) - 1:
                    if np.abs(vs[arglist[i]]) - np.abs(vs[arglist[i+1]]) >= self.find_threshold(i+1):
                        n = i+1
                        break
        if n != -1:
            for j in arglist[:n]:
                if vs[j] > 0:
                    limits[str(j)] = 'inf'
                else:
                    limits[str(j)] = 'zero'

            if len(self.limit_seq) == 0:
                self.limit_seq.append(limits)
            elif self.limit_seq[-1] == limits:
                self.limit_seq.append(limits)
            else:
                self.limit_seq = [limits]

    def find_threshold(self, n):
        """The threshold set to determine what velocities are defined as approaching
        a limit.

        Parameters
        ----------
        n : ``int``
            The nth parameter being checked.
        """
        return .5*(1/np.sqrt(n) + 1/np.sqrt(n+1))
