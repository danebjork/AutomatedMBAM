# AutomatedMBAM
A framework for automating the Manifold Boundary Approximation Method. This includes
reparameterizing the model using templates stored in MongoDB as well as several algorithms for evaluating
variable limits (singular limits).

This project contains an Engine, which attempts to approximate
a model automatically, as well as a User-Interface, which allows the user more
freedom when approximating her models.

# Engine Example
```python
import mbam
Load json model
model = mbam.engine(model_path, data_path)
model.run() # runs the geodesic
limits = [{"p1": "inf"}]
model.apply_limits(limits)
```

# Running the UI
The user interface is used to give more control over the approximation step.
It is run with a command in the terminal, followed by opening up the corresponding
HTML page.

## Locally
To run locally, run the command in the temrinal

```
python main.py
```

If successful, the terminal should show
```
Ready for Connection
```

Once the terminal is ready for a connection, open ./static/mbamui.html with
your favorite browser.

Any errors or problems will be reported to the terminal.


## Connecting to server
If you want to run the UI from a server, run the main.py script on the server.
On your local machine run the following command.

```
ssh -N -f -L localhost:9000:localhost:9000 user@server_address
```
Note: port 9000 is hard coded into the main.py as well as in the mbamui.html. Feel free to adjust the port as necessary.

When finished, run this command on your local machine to close the port.

```
sudo kill `sudo lsof -t -i:9000`
```

# Motivation
Link to Thesis (Not online yet)

# Installation
### MongoDB
This implementation uses MongoDB. The installation guide can be found
[here!](https://docs.mongodb.com/manual/installation/)

### Windows
On windows, I suggest installing the beta version of the Linux bash shell on Windows.
[Here's a great guide I have used to install it.](https://www.howtogeek.com/249966/how-to-install-and-use-the-linux-bash-shell-on-windows-10/)

### Python 3
This version was created and tested on Python 3.6.
The dependencies include:
```terminal
pip install -r requirements.txt
```

### Julia
Install Julia v1.0
```julia
Pkg.add("ZMQ")
Pkg.add("Parameters")
Pkg.add("HDF5")
Pkg.add("JSON")
Pkg.add("https://pulsar.byu.edu/Modeling/Geometry.jl.git")
Pkg.add("https://pulsar.byu.edu/Modeling/Models.jl.git")
Pkg.add("https://pulsar.byu.edu/Modeling/ParametricModels.jl.git")
```

In addition, some recommended packages that may be useful for constructing models

``` julia
Pkg.add("https://pulsar.byu.edu/Modeling/SmoothApproximations.jl.git")
Pkg.add("https://pulsar.byu.edu/Modeling/ModularLM.jl.git")
Pkg.add("https://pulsar.byu.edu/Modeling/ExampleModels.jl.git")
```

# API Reference
The docs can be found [here.](http://automatedmbam.readthedocs.io/)

# Tests
The current tests can be run by using the Engine and the engine and the user interface
to approximate the models found under 'examples'.

# Contributors
Feel free to fork the repo and make any changes for you modeling pleasure!

# License
MIT License
