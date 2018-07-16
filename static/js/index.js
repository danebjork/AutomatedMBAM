// init variables
var w = window.innerWidth;
var h = window.innerHeight;

var model = {};


var paramButton = document.getElementById("params-selected");
var modelScript = document.getElementById("model-julia-code");
var geoScript = document.getElementById("j-geo");
// load graph tab for plotting
var graphTab = document.getElementById("geo-graphs");
// initialize websocket
GeoTab.loadOptions();
var ws = new WebSocket("ws://127.0.0.1:9000/"),
    messages = document.createElement('ul');


EvalTab.saveModelBtn.onclick = function(){
    EvalTab.saveNewModel();
    send = {"type": "manual-iter", "model": ModelTab.newModelData};
    ws.send(JSON.stringify(send));
}

function getData() {
    console.log("collecting");
    ws.send(JSON.stringify({"type": "collect"}));
};
// ****************** WORKSPACE BTNS

var applyParams = document.getElementById("eval-param-apply");
applyParams.onclick = function(){
    ws.send(JSON.stringify({"type": "apply-theta", "data": EvalTab.collectData()}))
}

var loadModelID = document.getElementById("model-load");
loadModelID.onclick = function(){
    model_id = document.getElementById("model-id").value;
    send = {"type": "load-model-id", "id": model_id};
    console.log(send);
    ws.send(JSON.stringify(send));
}

var substituteBtn = document.getElementById("substitute-btn");
substituteBtn.onclick = function(){
    // send parameters and workspace to Python
    // var toSend = {};
    // toSend.params = EvalTab.collectData();
    // toSend.eq = Workspace.getText();
    ws.send(JSON.stringify({"type": "ftheta", "data": EvalTab.collectData()}))
    ws.send(JSON.stringify({"type": "substitute", "eq": Workspace.getText()}));
    // ws.send(JSON.stringify(toSend));
    // Python substitutes out the parameters in the workspace
    // the new substituted equation is loaded into Workspace with undo available
}
var geoOptionBtn = document.getElementById("geo-options");
geoOptionBtn.onclick = function() {
    send = {
        "type": "geo-options",
        "options": GeoTab.getJuliaOptions(),
    };
    ws.send(JSON.stringify(send));
}
var juliaOptionBtn = document.getElementById("julia-options");
juliaOptionBtn.onclick = function() {
    send = {
        "type": "julia-options",
        "options": ModelTab.getJuliaOptions(),
    };
    ws.send(JSON.stringify(send));
}
var simplifyBtn = document.getElementById("simplify-btn");
simplifyBtn.onclick = function(){
    Workspace.simplify(ws);
}
var epsilonBtn = document.getElementById("epsilon-btn");
epsilonBtn.onclick = function() {
    Workspace.epsilon(ws);
}
var undoBtn = document.getElementById("undo-btn");
undoBtn.onclick = function() {
    Workspace.undo();
}
//
// var latex_eq = {};
// ****************** WORKSPACE BTNS

function killGeodesic() {
    clearInterval(interval);
    ws.send(JSON.stringify({"type": "geo-done"}));
    console.log("SEND KILL");
}

document.getElementById("geo-julia-run").onclick = function() {
    GeoGraphs.format(ModelTab.data.ps);
    ws.send(JSON.stringify({"type": "geo-start"}));
    interval = setInterval(getData, 500);
    $("#geo-graphs-btn").click();
}

document.getElementById("geo-julia-end").onclick = function() {
    killGeodesic();
}

function testAlgebra(){
    ws.send("test-alg");
}

function updateModel(){
    //****** THROW ERRORS FOR BAD MODEL SET UP HERE
    // Collect the Model from the UI
    ModelTab.collectUIData();
    EvalTab.fillVarTab(ModelTab.modelData.vs);
    // Send the Model to the backend
    console.log(ModelTab.data);
    ws.send(JSON.stringify({"type": "save", "md": ModelTab.data}));
    // ws.send(JSON.stringify(ModelTab.data));
    // Send the options for the Julia model
    // ws.send("julia-generate");
    // var model_options = ModelTab.getJuliaOptions();
    // model_options.weights = dataWeights;
    // ws.send(JSON.stringify(model_options));
    // var geo_options = GeoTab.getJuliaOptions();
    // ws.send(JSON.stringify(geo_options));
    // console.log("sent options");
}



var dataWeights = false;
var loadDataBtn = document.getElementById("model-data-btn");
function loadDataFile(event){
    var reader = new FileReader();
    reader.onloadend = function(event){
        console.log("HDF5");
        ws.send(JSON.stringify({"type": "hdf5"}))
        ws.send(event.target.result);
    };
    var input = event.target;
    reader.readAsArrayBuffer(input.files[0]);
}

loadDataBtn.addEventListener('change', loadDataFile, false);

var saveModelBtn = document.getElementById("model-save-tab");
saveModelBtn.onclick = function(){
    updateModel();
}

document.getElementById("geo-julia-update").onclick = function() {
    send = {
        "type": "geo-update",
        "script": GeoTab.getJuliaText(),
    }
    ws.send(JSON.stringify(send));
}

document.getElementById("model-julia-update").onclick = function() {
    send = {
        "type": "julia-update",
        "script": ModelTab.getJuliaText(),
    }
    ws.send(JSON.stringify(send));
}

////////////////// WEBSOCKET CALLBACKS //////////////////
var selectedEqs = {}
var interval = null;
var test = null;
var latexModel = {};
var newLatexModel = {};
var symModel = {};
ws.onmessage = function (event) {
    // console.log(event.data);
        var json_d = JSON.parse(event.data);
        console.log(json_d.type)
        // console.log(json_d);
        if (json_d.type == "load-model") {
            model = json_d.model;
            console.log("LOAD", model);
            EvalTab.resetAllUI();
            ModelTab.loadJSON(model);
            $("#main-model-tab").click();
            $("#model-general-click-tab").click();
            EvalTab.fillVarTab(ModelTab.modelData.vs);
            ModelTab.resizePlots();
            // ps.value = json_d.ps.toString().replace(/,/g, ", ");
            // depV.value = json_d.depV.toString().replace(/,/g, ", ");
            // deriv.value = json_d.deriv.toString().replace(/,/g, ", ");
            // eq.value = json_d.eq.toString().replace(/,/g, ",\n");
        }
        else if (json_d.type == "geo") {
            if (json_d.x != null) {
                if (json_d.x.length > 0) {
                    GeoGraphs.update(json_d);
                }
            }
        }
        else if (json_d.type == "geo-done"){
            EvalTab.loadParams(json_d.limits);
            // killGeodesic();
        }
        else if (json_d.type == "post-save") {
            latexModel = json_d.latex;
            newLatexModel = JSON.parse(JSON.stringify( latexModel ));
        }
        else if(json_d.type == "julia-scripts"){
            ModelTab.updateJuliaText(json_d.model);
            GeoTab.updateJuliaText(json_d.geo);
        }
        else if (json_d.type == "eq-indexes") {
            Equations.load(json_d,  latex_eq);
            MathJax.Hub.Typeset();
        }
        else if (json_d.type == "simplify") {
            Workspace.simplifyCallback(json_d);
        }
        else if (json_d.type == "epsilon") {
            Workspace.epsilonCallback(json_d);
        }
        else if (json_d.type == "substitute"){
            Workspace.substitute(json_d);
        }
        else if (json_d.type == "model-data"){
            json_d = json_d.data;
            if(json_d.weights.length > 0){
                dataWeights = true;
            }
            ModelTab.plotData(json_d);
        }
}

window.onresize = function(event) {
    GeoGraphs.resizePlots();
    ModelTab.resizePlots();
}

document.body.appendChild(messages);

GeoGraphs.init();
