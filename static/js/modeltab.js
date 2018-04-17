

var ModelTab = {};


// Create an empty model for updating
// ModelTab.modelData = {
//     'time': [],
//     'data': {'type': 'none', 'data': [], 'weights': []},
//     'parameters': [],
//     'variables': [],
//     'ic': {'substitutions': [], 'equations': []},
//     'rhs': {'substitutions': [], 'equations': []},
//     'obs': {'substitutions': [], 'equations': []},
//     'inputs': {'substitutions': [], 'equations': []},
// }
//
// ModelTab.updateAllData(data){
//     this.modelData.data = data.data;
//     this.model
//     this.modelData.parameters.concat(data.parameters);
//     this.modelData.variables.concat(data.variables);
//     this.modelData.ic.substitutions.concat(data.ic.substitutions);
//     this.modelData.ic.equations.concat(data.ic.equations);
//     this.modelData.rhs.substitutions.concat(data.ic.substitutions);
//     this.modelData.rhs.equations.concat(data.ic.equations);
//     this.modelData.obs.substitutions.concat(data.ic.substitutions);
//     this.modelData.obs.equations.concat(data.ic.equations);
//     this.modeldata.inp.substitutions.concat(data.ic.substitutions);
//     this.modeldata.inp.equations.concat(data.ic.equations);
// }

// ModelTab.saveBtn = document.getElementById("model-save-tab");
// ModelTab.saveBtn.onclick = function(){
//     ModelTab.collectUIData();
// }
ModelTab.data = {};
ModelTab.collectUIData = function(){
    this.collectGeneralData();
    this.collectParamData();
    this.collectVarData();
    // add IF ODE statement
    if (document.getElementById("model-type-select").value == "ODE") {
        this.data.ic = {};
        this.collectEqs("model-ic", this.data.ic);
        this.data.obs = {};
        this.collectEqs("model-obs", this.data.obs);
        this.data.rhs = {};
        this.collectEqs("model-rhs", this.data.rhs);
        this.data.inp = {};
        this.collectEqs("model-inputs", this.data.inp);
    }
    else if (document.getElementById("model-type-select").value == "DAE") {
        this.data.ic = {};
        this.collectEqs("model-dae-ic", this.data.ic);
        this.data.icd = {}
        this.collectDAEICD(this.data.icd);
        this.data.obs = {};
        this.collectEqs("model-obs", this.data.obs);
        this.data.res = {};
        this.collectEqs("model-res", this.data.res);
        this.data.inp = {};
        this.collectEqs("model-inputs", this.data.inp);
    }
    console.log(this.data);
}

// ********* GENERAL TAB ***************
ModelTab.name = document.getElementById("model-name");
ModelTab.class = document.getElementById("model-class");
ModelTab.loadModelBtn = document.getElementById("model-load-btn");

ModelTab.functionTabList = [
    "model-general-tab",
    "model-data-tab",
    "model-parameters-tab",
    "model-variables-tab",
    "model-julia-tab",
    "model-save-tab",
];

ModelTab.ODETabList = [
    "model-general-tab",
    "model-data-tab",
    "model-parameters-tab",
    "model-variables-tab",
    "model-inputs-tab",
    "model-ic-tab",
    "model-rhs-tab",
    "model-obs-tab",
    "model-julia-tab",
    "model-save-tab",
];

ModelTab.DAETabList = [
    "model-general-tab",
    "model-data-tab",
    "model-parameters-tab",
    "model-variables-tab",
    "model-inputs-tab",
    "model-icd-tab",
    "model-res-tab",
    "model-obs-tab",
    "model-julia-tab",
    "model-save-tab",
];

ModelTab.collectGeneralData = function(){
    this.data.name = this.name.value;
    this.data.class = this.class.value;
    this.data.type = document.getElementById("model-type-select").value;
    this.data.julia = {};
}

ModelTab.getJuliaOptions = function(){
    var options = {};
    options.bare = document.getElementById("model-bare-opt").checked;
    options.weights = this.data.weights.length > 0;
    return options;
}

ModelTab.loadFile = function(event){
    ModelTab.clear();
    var reader = new FileReader();
    reader.onload = function(){
        var d = JSON.parse(reader.result);
        console.log(d);
        // ModelTab.updateAllData(d);
        ModelTab.loadJSON(d);
    };
    var input = event.target;
    reader.readAsText(input.files[0]);
}

ModelTab.loadJSON = function(d){
    console.log("LOADING MODEL");
    ModelTab.modelData = d;
    ModelTab.newModelData = JSON.parse(JSON.stringify(d));
    d.type = d.type.toUpperCase();
    ModelTab.typeSelect.value = d.type;
    ModelTab.name.value = d.name;
    ModelTab.class.value = d.class;
    ModelTab.showValueTabs(d.type);
    Workspace.showButtons(d.type);
    ModelTab.fillParamTab(d.ps);
    ModelTab.fillVarTab(d.vs);
    if (d.type.toLowerCase() == "ode"){
        ModelTab.loadEqs("model-ic", d.ic);
        ModelTab.loadEqs("model-rhs", d.rhs);
        ModelTab.loadEqs("model-obs", d.obs);
        ModelTab.loadEqs("model-inputs", d.inp);
    }
    if (d.type.toLowerCase() == "dae"){
        ModelTab.loadDAEIC(d);
        ModelTab.loadEqs("model-res", d.res);
        ModelTab.loadEqs("model-obs", d.obs);
        ModelTab.loadEqs("model-inputs", d.inp);
    }
}

ModelTab.collectDAEICD = function(storage){
    storage.sbs = [];
    storage.eqs = this.collectFromInput("model-dae-icd-eqs");
}

ModelTab.collectEqs = function(id, storage){
    var subs = this.collectFromInput(id + "-subs");
    storage.sbs = subs;
    var eqs = this.collectFromInput(id + "-eqs");
    storage.eqs = eqs;
}

ModelTab.collectFromInput = function(id){
    var eqUI = document.getElementById(id);
    var eq = eqUI.value.replace(/\n/g, ",").replace(/\s/g, "").split(',');
    if(eq[eq.length-1] == ""){
        eq.pop();
    }
    return eq.filter(Boolean);
}

ModelTab.loadEqs = function(id, eqs){
    console.log("LOADING: ", id);
    var subsUI = document.getElementById(id + "-subs");
    var eqsUI = document.getElementById(id + "-eqs");
    subsUI.value = this.createEqText(eqs.sbs);
    eqsUI.value = this.createEqText(eqs.eqs);
}

ModelTab.loadDAEIC = function(dae){
    var subsUI = document.getElementById("model-dae-ic-subs");
    var eqsIC = document.getElementById("model-dae-ic-eqs");
    var eqsICD = document.getElementById("model-dae-icd-eqs");
    subsUI.value = this.createEqText(dae.ic.sbs);
    eqsIC.value = this.createEqText(dae.ic.eqs);
    eqsICD.value = this.createEqText(dae.icd.eqs);
}

ModelTab.clearEqs = function(id){
    document.getElementById(id + "-subs").value = "";
    document.getElementById(id + "-eqs").value = "";
}

ModelTab.createEqText = function(eqs){
    var text = ""
    for (var e in eqs){
        text += eqs[e]
        if(e != eqs.length){
            text += "\n"
        }
    }
    return text
}

ModelTab.loadModelBtn.addEventListener('change', ModelTab.loadFile, false);

ModelTab.typeSelect = document.getElementById("model-type-select");

ModelTab.tabList = document.getElementById("model-tab-list");

ModelTab.typeSelect.onchange = function(){
    // ModelTab.hideAllTabs();
    ModelTab.showValueTabs(this.value);
    Workspace.showButtons(this.value);
}

ModelTab.hideAllTabs = function(){
    for (var key in this.tabList.children){
        var child = this.tabList.children[key];
        if(child.tagName == "LI"){
            if(child.children[0].id != "model-general-tab" &&
            child.children[0].id != "model-save-tab" &&
        child.children[0].id != "model-data-tab"){
                child.children[0].style.display = "none";
            }
        }
    }
}

ModelTab.showValueTabs = function(value){
    if(value == "function"){
        this.showListedTabs(this.functionTabList);
    }
    else if (value == "ODE"){
        this.showListedTabs(this.ODETabList);
    }
    else if (value == "DAE"){
        this.showListedTabs(this.DAETabList);
    }
}

ModelTab.showListedTabs = function(list){
    for (var key in this.tabList.children){
        var child = this.tabList.children[key];
        if(child.tagName == "LI"){
            if(list.indexOf(child.id) != -1){
                child.style.display = "";
            }
            else {
                child.style.display = "none";
            }
        }
    }
}


// ********** PARAM TAB ***********

ModelTab.paramList = document.getElementById("model-param-list");
ModelTab.paramSearch = document.getElementById("model-param-search");
ModelTab.removeParamBtn = document.getElementById("model-param-remove-btn");
$("#model-param-remove-btn").button("disable");
ModelTab.transformList = ['constant', 'identity', 'log', 'sinh'];


ModelTab.findNonconstantParam = function(index){
    var i = 0;
    index = parseInt(index);
    for (var key in ModelTab.modelData.ps){
        console.log();
        if(ModelTab.modelData.ps[key].transform != "constant"){
            if(i == index){
                return ModelTab.modelData.ps[key].name;
            }
            i += 1;
        }
    }
    return null;
}

var visibleParams = []

ModelTab.removeParamBtn.onclick = function() {
    console.log(visibleParams);
    var child = document.getElementById(visibleParams[0].id);
    ModelTab.paramList.removeChild(child);
    ModelTab.paramSearch.value = "";
    searchParams("");
}

ModelTab.collectParamData = function(){
    this.data.ps = [];
    for(var child in this.paramList.children){
        if (this.paramList.children[child].tagName == "LI"){
            var pdata = this.collectSingleParamData(this.paramList.children[child]);
            this.data.ps.push(pdata);
        }
    }
}

ModelTab.collectSingleParamData = function(li){
    var pdata = {
        'name': li.children[0].value.replace(/\s/g, ""),
        'transform': li.children[1].value,
        'init_val': li.children[2].value.replace(/\s/g, ""),
    }
    return pdata;
}

$("#model-param-search").bind('input', function() {
    var text = $(this).val();
    searchParams(text);
});

function searchParams(text){
    if (text.length == 0){
        ModelTab.showAllListItems(ModelTab.paramList);
        $("#model-param-remove-btn").button("disable");
        visibleParams = []; // should all be shown, but the UI reacts the same
    }
    else if (text == parseInt(text)){
        console.log("INDEX");
        visibleParams = ModelTab.showOnlyIndexedItem(parseInt(text), ModelTab.paramList)
    }
    else{
        visibleParams = ModelTab.showFilteredListItems(text, ModelTab.paramList);
    }
    console.log(visibleParams);
    if(visibleParams.length == 1) {
        $("#model-param-remove-btn").button("enable");
    }
    else {
        $("#model-param-remove-btn").button("disable");
    }
}

ModelTab.showOnlyIndexedItem = function(index, list){
    var found = []
    for (var child in list.children){
        if (list.children[child].tagName == "LI"){
            if((parseInt(child) + 1)== index){
                list.children[child].style.display = "inline-block";
                found.push(list.children[child])
            }
            else{
                list.children[child].style.display = "none";
            }
        }
    }
    return found;
}

ModelTab.showAllListItems = function(list){
    for (var child in list.children){
        if (list.children[child].tagName == "LI"){
            list.children[child].style.display = "inline-block";
        }
    }
}

ModelTab.showFilteredListItems = function(text, list){
    var found = []
    for (var child in list.children){
        if (list.children[child].tagName == "LI"){
            var id = list.children[child].id;
            var pname = id.substring(id.lastIndexOf('-')+1, id.length);
            if(pname.toLowerCase().indexOf(text.toLowerCase()) != -1){
                found.push(list.children[child])
                list.children[child].style.display = "inline-block";
            }
            else {
                list.children[child].style.display = "none";
            }
        }
    }
    return found;
}

ModelTab.fillParamTab = function(params){
    for (var p in params){
        this.addSingleParamTab(params[p]);
    }
}

ModelTab.addSingleParamTab = function(param){
    var li = document.createElement("LI");
    li.className = "model-item";
    li.id = "model-param-" + param.name;
    var paramName = document.createElement("INPUT");
    paramName.className = "model-item";
    paramName.value = param.name;

    var initVal = document.createElement("INPUT");
    initVal.className = "model-item"
    initVal.value = param.init_val;

    li.appendChild(paramName);
    li.appendChild(this.createSelector(this.transformList, param.transform))
    li.appendChild(initVal);

    this.paramList.appendChild(li);
}


ModelTab.createSelector = function(options, choice){
    var selector = document.createElement("SELECT");
    selector.className = "model-item";
    for (var opt in options){
        var o = document.createElement("OPTION");
        o.value = options[opt]
        o.innerText = options[opt]
        selector.appendChild(o);
    }
    selector.value = choice;
    return selector

}

document.getElementById("model-param-add").onclick = function(){
    ModelTab.addParamDialog.dialog("open");
}

ModelTab.addParam = function(){
    console.log("ADDED");
    var name = document.getElementById("new-param-name").value;
    var transform = document.getElementById("new-param-transform").value;
    var initVal = document.getElementById("new-param-init-val").value;
    // 'init_val': 1.5, 'name': 'x10', 'transform': 'constant'
    var newParam = {
        'init_val': initVal,
        'name': name,
        'transform': transform,
    }
    ModelTab.addSingleParamTab(newParam);
    ModelTab.addParamDialog.dialog("close");
}


ModelTab.addParamDialog = $( "#model-param-dialog" ).dialog({
  autoOpen: false,
  width: 400,
  modal: true,
  buttons: {
    "Add Parameter": ModelTab.addParam,
    Cancel: function() {
      ModelTab.addParamDialog.dialog( "close" );
    }
  },
  close: function() {
      console.log("reset")
    addParamForm[ 0 ].reset();
  }
});

addParamForm = ModelTab.addParamDialog.find( "form" ).on( "submit", function( event ) {
  event.preventDefault();
  console.log("form");
  ModelTab.addParam();
});

// ********* VARIABLE TAB ***************
ModelTab.varList = document.getElementById("model-var-list");
ModelTab.varTypeList = ['algebraic', 'dynamic'];
ModelTab.removeVarBtn = document.getElementById("model-var-remove-btn");
$("#model-var-remove-btn").button("disable");
ModelTab.varSearch = document.getElementById("model-var-search");
var visibleVars = []

ModelTab.removeVarBtn.onclick = function() {
    console.log(visibleVars);
    var child = document.getElementById(visibleVars[0].id);
    ModelTab.varList.removeChild(child);
    ModelTab.varSearch.value = "";
    searchVars("");
}

function searchVars(text){
    if (text.length == 0){
        ModelTab.showAllListItems(ModelTab.varList);
        $("#model-var-remove-btn").button("disable");
        visibleVars = []; // should all be shown, but the UI reacts the same
    }
    else if (text == parseInt(text)){
        console.log("INDEX");
        visibleVars = ModelTab.showOnlyIndexedItem(parseInt(text), ModelTab.varList)
    }
    else{
        visibleVars = ModelTab.showFilteredListItems(text, ModelTab.varList);
    }
    console.log(visibleVars);
    if(visibleVars.length == 1) {
        $("#model-var-remove-btn").button("enable");
    }
    else {
        $("#model-var-remove-btn").button("disable");
    }

    // if (text.length == 0){
    //     ModelTab.showAllListItems(ModelTab.varList);
    //     ModelTab.removeVarBtn.disabled = true;
    // }
    // else{
    //     visibleVars = ModelTab.showFilteredListItems(text, ModelTab.varList);
    //     console.log(visibleVars);
    //     if(visibleVars.length == 1) {
    //         ModelTab.removeVarBtn.disabled = false;
    //     }
    //     else {
    //         ModelTab.removeVarBtn.disabled = true;
    //     }
    // }
}

ModelTab.collectVarData = function(){
    this.data.vs = [];
    for(var child in this.varList.children){
        if (this.varList.children[child].tagName == "LI"){
            var vdata = this.collectSingleVarData(this.varList.children[child]);
            this.data.vs.push(vdata);
        }
    }
}

ModelTab.collectSingleVarData = function(li){
    var vData = {
        'name': li.children[0].value.replace(/\s/g, ""),
        'type': li.children[1].value,
    }
    return vData
}

$("#model-var-search").bind('input', function() {
    var text = $(this).val();
    searchVars(text);
});

ModelTab.fillVarTab = function(vars) {
    for(var v in vars){
        this.addSingleVarTab(vars[v]);
    }
}

ModelTab.addSingleVarTab = function(myVar){
    var li = document.createElement("LI");
    li.className = "model-item";
    li.id = "model-var-" + myVar.name;
    var varName = document.createElement("INPUT");
    varName.className = "model-item";
    varName.value = myVar.name;
    li.appendChild(varName);
    li.appendChild(this.createSelector(this.varTypeList, myVar.type))
    this.varList.appendChild(li);
}

document.getElementById("model-var-add").onclick = function(){
    ModelTab.addVarDialog.dialog("open");
}

ModelTab.addVar = function(){
    console.log("ADDED");
    var name = document.getElementById("new-var-name").value;
    var type = document.getElementById("new-var-type").value;
    // 'init_val': 1.5, 'name': 'x10', 'transform': 'constant'
    var newVar = {
        'type': type,
        'name': name,
    }
    ModelTab.addSingleVarTab(newVar);
    ModelTab.addVarDialog.dialog("close");
}


ModelTab.addVarDialog = $( "#model-var-dialog" ).dialog({
  autoOpen: false,
  width: 400,
  modal: true,
  buttons: {
    "Add Variable": ModelTab.addVar,
    Cancel: function() {
      ModelTab.addVarDialog.dialog( "close" );
    }
  },
  close: function() {
    addVarForm[ 0 ].reset();
  }
});

addVarForm = ModelTab.addVarDialog.find( "form" ).on( "submit", function( event ) {
  event.preventDefault();
  console.log("form");
  ModelTab.addVar();
});

// ********* JULIA MODEL CODE TAB **************

ModelTab.juliaEditor = ace.edit("model-julia-editor");
ModelTab.juliaEditor.setTheme("ace/theme/tomorrow");
ModelTab.juliaEditor.session.setMode("ace/mode/julia");
ModelTab.juliaEditor.resize()
ModelTab.updateJuliaText = function(text){
    this.juliaEditor.setValue(text);
}

ModelTab.getJuliaText = function() {
    return this.juliaEditor.getValue();
}
// ********** MODEL DATA TAB ******************

function random_color() {
  var r = Math.random();
  r = 200*r + 40;
  r = Math.floor(r);

  var g = Math.random();
  g = 200 * g + 40;
  g = Math.floor(g);

  var b = Math.random();
  b = 200 * b + 40;
  b = Math.floor(b);
  var color = r + "," + g + "," + b;
  return color;
}

ModelTab.dataTraces = [];
function iterate_json(json){
    ModelTab.data.ydata = json.ydata;
    ModelTab.data.time = json.t;
    ModelTab.data.weights = json.weights;
    for (var key in json.ydata){
        var color = random_color();
        var jIndex = parseInt(key)+1;
        var label = "y[" + jIndex+ "]";
        ModelTab.dataTraces.push(create_trace(json.t, json.ydata[key], label, "rgb(" + color+")"));
        if (json.weights.length != 0) {
            ModelTab.dataTraces.push(create_weights_trace(json.t, json.ydata[key], json.weights[key], label, "rgba("+color+",0.2)"));
        }
    }
}

function create_trace(time, data, label, mycolor){
    var trace = {
        x: time,
        y: data,
        mode:"lines",
        legendgroup: label,
        line: {color: mycolor},
        name: label,
        type: "scatter",
    };
    return trace;
}

function margin_times(time){
    return time.concat(time.slice().reverse());
}

function upper_bound(data, weights){
    var upper = [];
    for(var i = 0; i < data.length; i++) {
        upper.push(data[i] + 1/weights[i]);
    }
    return upper;
}

function lower_bound(data, weights){
    var lower = [];
    for(var i = 0; i < data.length; i++) {
        lower.push(data[i] - 1/weights[i]);
    }
    return lower.reverse();
}

function create_weights_trace(time, data, weights, label, mycolor){
    var trace = {
        x: margin_times(time),
        y: upper_bound(data, weights).concat(lower_bound(data, weights)),
        fill: "tozerox",
        fillcolor: mycolor,
        name: label,
        legendgroup: label,
        line: {color: "transparent"},
        showlegend: false,
        type: "scatter",
    }
    return trace;
}
ModelTab.plotData = function(json){
    var dataLayout = {
      hovermode:'closest',
      xaxis: {
        showgrid: true,
        showticklabels: true,
        tickcolor: "rgb(127,127,127)",
        ticks: "outside",
      },
      yaxis: {
        showgrid: true,
        showticklabels: true,
        tickcolor: "rgb(127,127,127)",
        ticks: "outside",
      }
    };
    iterate_json(json);
    Plotly.newPlot("model-data-graph", ModelTab.dataTraces, dataLayout);
}

// ModelTab.dataTab = document.getElementById("model-data-btn");
// ModelTab.dataTab.onclick = function(){
//     ModelTab.resizePlots();
// }

ModelTab.resizePlots = function(){
    Plotly.Plots.resize(document.getElementById("model-data-graph"));
}

ModelTab.clear = function(){
    ModelTab.name.value = "";
    ModelTab.class.value = "";
    ModelTab.typeSelect.value = "";
    ModelTab.paramList.innerHTML = "";
    ModelTab.varList.innerHTML = "";
    ModelTab.clearEqs("model-ic");
    ModelTab.clearEqs("model-rhs");
    ModelTab.clearEqs("model-obs");
    ModelTab.clearEqs("model-inputs");
    ModelTab.updateJuliaText("");
}
