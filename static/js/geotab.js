var GeoTab = {};

// GENERAL TAB***********
GeoTab.options = {
    "tmax": "1.0",
    "lambda": "0.0",
    "abstol": 1e-3,
    "reltol": 1e-3,
    "use_svd": false,
    "use_pinv": false,
}

GeoTab.graphsTab = document.getElementById("geo-graphs-btn");
GeoTab.graphsTab.onclick = function(){
    GeoGraphs.resizePlots();
}

GeoTab.optionsList = document.getElementById("geo-options-list");

GeoTab.getJuliaOptions = function(){
    var options = {};
    for (var opt in GeoTab.optionsList.children){
        var li = GeoTab.optionsList.children[opt];
        if(li.tagName == "LI"){
            if(li.children[1].tagName == "LABEL"){
                options[li.children[1].innerText] = li.children[0].checked;
            }
            else{
                options[li.children[0].value] = li.children[1].value;
            }
        }
    }
    return options;
}

GeoTab.loadOptions = function(){
    GeoTab.optionsList.innerHTML = "";
    for (var opt in GeoTab.options){
        if(typeof(GeoTab.options[opt]) == "number" || typeof(GeoTab.options[opt]) == "string"){
            GeoTab.optionsList.appendChild(GeoTab.createValueOption(opt, GeoTab.options[opt]));
        }
        else if(typeof(GeoTab.options[opt]) == "boolean"){
            GeoTab.optionsList.appendChild(GeoTab.createBoolOption(opt, GeoTab.options[opt]));
        }
    }
}
// fill in the options list
GeoTab.createValueOption = function(name, defaultVal){
    var li = document.createElement("LI");
    li.id = name;
    li.className = "model-item";

    var nameInput = document.createElement("INPUT");
    nameInput.value = name;

    var valInput = document.createElement("INPUT");
    valInput.value = defaultVal;

    var textNode = document.createTextNode("=");
    li.appendChild(nameInput);
    li.appendChild(textNode);
    li.appendChild(valInput);
    return li;
}

GeoTab.createBoolOption = function(name, defaultVal){
    var li = document.createElement("LI");
    li.id = name;
    li.className = "model-item";
    var label = document.createElement("LABEL");
    label.innerText = name;
    label.for = name+"_check";
    var input = document.createElement("INPUT");
    input.type = "checkbox";
    input.checked = defaultVal;
    input.id = name+"_check";
    li.appendChild(input);
    li.appendChild(label);
    return li;
}

// JULIA SCRIPT TAB**********

GeoTab.juliaEditor = ace.edit("geo-julia-editor");
GeoTab.juliaEditor.setTheme("ace/theme/tomorrow");
GeoTab.juliaEditor.session.setMode("ace/mode/julia");
GeoTab.juliaEditor.resize()
GeoTab.updateJuliaText = function(text){
    this.juliaEditor.setValue(text);
}
GeoTab.getJuliaText = function(){
    return this.juliaEditor.getValue();
}

GeoTab.clear = function(){
    this.loadOptions();
    this.updateJuliaText("");
    GeoGraphs.clear();
}

var limitTest = {"2": "infinity"};
