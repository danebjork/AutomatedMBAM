
import os

### ALL JULIA SCRIPTS ONLY USE " " FOR STRINGS, SO USE ' ' FOR PYTHON PARSING TO JULIA.
class GeodesicParser:
    def __init__(self, mbam_model, model_path, collector_path):
        """
        Parameters
        ----------
        mbam_model : ``mbammodel``
            Can be any of the following: Function, ODE, DAE.
        model_path : ``str``
            The full path to the corresponding julia model file.
        collector_path : ``str``
            Full path to 'geosender.jl' for sending the data to MongoDB.
        """
        self.model_path = model_path
        self.mm = mbam_model
        self.collector_path = collector_path
        self.default_options()
        self.dir = os.path.join("julia_scripts", "geos")
        # self.dir = "julia_scripts"
        # Need to figure out naming convention for several models of same type & param num
        self.model_name = self.mm.name
        self.file_name = self.model_name + ".jl"
        self.file_path = os.path.join(self.dir, self.file_name)
        self.write_geo_script()
        self.save_to_file(self.script)

    def default_options(self):
        """ Used until options are updated with update_options
        """
        self.options = {
            "tmax": 1.0,
            "lambda": 0.0,
            "abstol": 1e-3,
            "reltol": 1e-3,
            "use_svd": False,
            "use_pinv": False,
        }

    def update_options(self, options):
        """Creates and saves a new script generated with the given options.

        Parameters
        ----------
        options : ``dict``
            Must follow format:

            {

                "tmax": ``float``,

                "lambda": ``float``,

                "abstol": ``float``,

                "reltol": ``float``,

                "use_svd": ``bool``,

                "use_pinv": ``bool``,

            }

        """
        self.options = options
        self.write_geo_script()
        self.save_to_file(self.script)

    def init_geos_dir(self):
        if not os.path.exists(self.dir):
            os.makedirs(self.dir)

    def save_to_file(self, script):
        self.init_geos_dir()
        with open(self.file_path, "w", encoding="utf-8") as jl:
            jl.write(script)

    def write_geo_script(self):
        self.script = ''
        self.script += self.init_script()
        self.script += self.geo_loop()
        self.script += self.end_script()

    def init_script(self):
        ret = 'module T\n'
        ret += 'import Models\n'
        ret += 'import Geometry\n'

        # changing file referencing to relative file paths!
        # ret += 'include("{0}")\n'.format(self.model_path)
        ret += 'include("{0}")\n'.format(os.path.join(os.pardir, 'models', self.file_name)).replace("\\", "\\\\")
        # ret += 'include("{0}")\n'.format(self.collector_path)
        ret += 'include("{0}")\n'.format(os.path.join(os.pardir, os.pardir, 'geosender.jl')).replace("\\", "\\\\")

        ret += 'model = {0}_Model.model\n'.format(self.model_name)
        ret += 'xi = {0}_Model.xi\n'.format(self.model_name)
        ret += 'v = Geometry.Geodesics.vi(xi, model.jacobian, model.Avv)\n'
        # Add function to include options here in integrator
        ret += 'integrator = Models.GeodesicIntegrator(model, xi, v, '
        ret += self.load_options() + ")\n"
        ret += 'start = Dict("x"=> [], "v"=> [], "tau"=> [], "t"=> [], "j"=>[])\n'
        # ret += 'GeoSender.send_to_py("start", start)\n'
        return ret

    def load_options(self):
        to_ret = ''
        for i, opt in enumerate(self.options):
            to_ret += opt
            to_ret += "="
            if (isinstance(self.options[opt], bool)):
                if(self.options[opt]):
                    to_ret += "true"
                else:
                    to_ret += "false"
            else:
                to_ret += str(self.options[opt])
            if i != len(self.options)-1:
                to_ret += ", "
        return to_ret


    def geo_loop(self):
        ret = 'try\n'
        ret += '\twhile true\n'
        ret += '\t\tGeometry.Geodesics.step!(integrator)\n'
        ret += '\t\tsol = Geometry.Geodesics.solution(integrator)\n'
        ret += '\t\tj = model.jacobian(sol.xs[end, :])\n'
        ret += '\t\tupdate = Dict(\n'
        ret += '\t\t\t"x"=>sol.xs[end, :],\n'
        ret += '\t\t\t"v"=>sol.vs[end, :],\n'
        ret += '\t\t\t"tau"=>sol.τs[end, :],\n'
        ret += '\t\t\t"t"=>sol.ts[end, :],\n'
        ret += '\t\t\t"j"=>j,\n'
        ret += '\t\t)\n'
        ret += '\t\tpush = false\n'
        ret += '\t\twhile !push\n'
        ret += '\t\t\ttry\n'
        ret += '\t\t\t\tGeoSender.send_to_py(update)\n'
        ret += '\t\t\t\tpush = true\n'
        ret += '\t\t\tcatch\n'
        ret += '\t\t\t\tsleep(.4)\n'
        ret += '\t\t\tend\n'
        ret += '\t\tend\n'
        ret += '\tend\n'
        return ret

    def end_script(self):
        ret = 'catch E\n'
        # ret += '\tGeoSender.send_to_py("end", Dict())\n'
        ret += '\tprintln(E)\n'
        ret += '\tGeoSender.send_to_py(Dict("done"=> "except"))\n'
        ret += 'end\n'
        ret += 'end # module'
        return ret
