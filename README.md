# AutomatedMBAM
A framework for automating the Manifold Boundary Approximation Method. This includes
reparameterizing the model using templates stored in MongoDB as well as evaluating
singular limits.

This project contains an Engine, which attempts to approximate
a model automatically, as well as a User-Interface, which allows the user more
freedom when approximating her models.

# Engine Example
Import mbam
Load json model
model = mbam.engine(model_path, data_path)
model.run() # runs the geodesic
limits = [{"p1": "inf"}]
model.apply_limits(limits)

# Running the UI

## Locally

## Connecting to server
ssh -N -f -L localhost:9000:localhost:9000 dane@bolyai.byu.edu
sudo kill `sudo lsof -t -i:9000`

# Motivation
Link to Thesis

# Installation
### MongoDB
This implementation uses MongoDB. The installation guide can be found
[here!](https://docs.mongodb.com/manual/installation/)

### Python 3
This version was created and tested on Python 3.6.
The dependencies include:
```python
pip install tables
pip install zmq
pip install pymongo
pip install sympy
pip install numpy
pip install WebSockets
```
A setup.py file should be created to do this automatically...

### Julia
Install Julia v0.6
```julia
Pkg.add("ZMQ")
```
Other packages need to be installed. These are currently not open sourced.
However, if the limits of the models are known, this project can still be used, only
the geodesic cannot be evaluated.


# API Reference
Reference docs

# Tests
The current tests can be run by using the Engine and the engine and the user interface
to approximate the models found under 'examples'.

# Contributors
Feel free to fork the repo and make any changes for you modeling pleasure!

# License
MIT License
