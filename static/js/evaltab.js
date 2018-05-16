var EvalTab = {}

EvalTab.newModelInput = document.getElementById("eval-model-name");
EvalTab.saveModelBtn = document.getElementById("eval-save-btn");
EvalTab.UIList = document.getElementById("param-redef-list");
EvalTab.UIList.style.borderLeft = "1pt solid";
EvalTab.UIList.style.borderRight = "1pt solid";
EvalTab.UIList.style.borderBottom = "1pt solid";
EvalTab.data = [];
EvalTab.params = [];

EvalTab.collectData = function() {
    this.data = [];
    for(var i in this.UIList.children){
        var child = this.UIList.children[i];
        if(child.tagName == "DIV"){
            if(child.children[1].children[0].value != "none"){
                lim = {}
                lim['theta'] = child.children[0].children[0].value
                lim['limit'] = child.children[1].children[0].value
                lim['tilde'] = child.children[2].children[0].value
                lim['f'] = child.children[3].children[0].value
                this.data.push(lim)
            }
        }
    }
    return this.data;
}

// EvalTab.searchForParams = function(websocket){
//     this.collectData();
//     websocket.send("find-params");
//     websocket.send(JSON.stringify(this.data.theta))
// }

EvalTab.resetTab = function() {
    this.UIList.innerHTML = "";
}

EvalTab.loadTheta = function(paramName){
    var div = this.createInnerDiv("10%");
    var input = this.createInput("90%");
    input.value = paramName;
    input.id = "theta-" + paramName;
    div.appendChild(input);
    return div
}

EvalTab.loadLimit = function(paramName, limit){
    var div = this.createInnerDiv("10%");
    var select = document.createElement("SELECT");
    select.id = "limit-" + paramName;
    select.style.marginTop = "7pt";
    select.style.width = "100%";
    select.appendChild(this.createNoneOption());
    select.appendChild(this.createZeroOption());
    select.appendChild(this.createInfinityOption());
    select.value = limit;
    div.appendChild(select);
    return div;
}

EvalTab.loadThetaTilde = function(paramName){
    var div = this.createInnerDiv("10%");
    var input = this.createInput("90%");
    input.id = "tilde-" + paramName;
    div.appendChild(input);
    return div
}

EvalTab.loadFTheta = function(paramName){
    var div = this.createInnerDiv("40%");
    var input = this.createInput("97.5%");
    input.id = "f-" + paramName;
    div.appendChild(input);
    return div
}

EvalTab.createZeroOption = function() {
    var opt = document.createElement("OPTION");
    opt.value = "zero";
    opt.innerText = "Zero";
    return opt
}

EvalTab.createInfinityOption = function() {
    var opt = document.createElement("OPTION");
    opt.value = "inf";
    opt.innerText = "Infinity";
    return opt
}
EvalTab.createNoneOption = function() {
    var opt = document.createElement("OPTION");
    opt.value = "none";
    opt.innerText = "None";
    return opt
}

EvalTab.createInnerDiv = function(width){
    var div = document.createElement("DIV");
    div.style.width = width;
    div.style.float = "left";
    return div;
}

EvalTab.createInput = function(width){
    var input = document.createElement("INPUT");
    input.style.width = width;
    input.style.margin = "5pt";
    return input;
}

EvalTab.createRemoveBtn = function(name){
    var btn = document.createElement("BUTTON");
    btn.className = "eq-btn";
    btn.innerText = "Remove";
    btn.id = "BTN-" + name;
    btn.onclick = function(){
        document.getElementById("DIV-"+name).remove();
        EvalTab.colorTable();
    };
    return btn;
}

EvalTab.colorTable = function(){
    console.log("HERE");
    for(var child in EvalTab.UIList.children){
        if(EvalTab.UIList.children[child].tagName == "DIV"){
            if(parseInt(child) % 2 == 1){
                EvalTab.UIList.children[child].style.backgroundColor = "#e6e6e6";
            }
            else{
                EvalTab.UIList.children[child].style.backgroundColor = "#ffffff";
            }
        }
    }
}

EvalTab.addParam = function(name, limit){
    var parentDiv = document.createElement("DIV");
    parentDiv.id = "DIV-" + name;
    parentDiv.style.width = "100%";
    parentDiv.style.height = "33pt";
    parentDiv.appendChild(this.loadTheta(name));
    parentDiv.appendChild(this.loadLimit(name, limit));
    parentDiv.appendChild(this.loadThetaTilde(name));
    parentDiv.appendChild(this.loadFTheta(name));
    parentDiv.appendChild(this.createRemoveBtn(name));
    parentDiv.style.borderTop = "1pt solid";
    if ( this.UIList.children.length % 2 == 1) {
        parentDiv.style.backgroundColor = "#e6e6e6";
    }
    this.UIList.appendChild(parentDiv);
    $( ".eq-btn" ).button();
}

document.getElementById("eval-add-param-btn").onclick = function(){
    EvalTab.addParam("", "none");
}

EvalTab.loadParams = function(limitList){
    this.resetTab();
    EvalTab.params = [];
    // EvalTab.params = paramList;
    for (var key in limitList){
        name = ModelTab.findNonconstantParam(key);
        EvalTab.addParam(name, limitList[key]);
        EvalTab.params.push(name);
    }
}

// EvalTab.loadParams(GeoTab.limitTest);

// ********* VARIABLE TAB ***************
EvalTab.varList = document.getElementById("eval-var-list");
EvalTab.varTypeList = ['algebraic', 'dynamic'];
EvalTab.removeVarBtn = document.getElementById("eval-var-remove-btn");
$("#eval-var-remove-btn").button("disable");
EvalTab.varSearch = document.getElementById("eval-var-search");
var visibleVars = []

EvalTab.removeVarBtn.onclick = function() {
    console.log(visibleVars);
    var child = document.getElementById(visibleVars[0].id);
    EvalTab.varList.removeChild(child);
    EvalTab.varSearch.value = "";
    EvalTab.searchVars("");
}

EvalTab.searchVars = function(text){
    console.log("EVAL SEARCH");
    if (text.length == 0){
        EvalTab.showAllListItems(EvalTab.varList);
        $("#eval-var-remove-btn").button("disable");
        visibleVars = []; // should all be shown, but the UI reacts the same
    }
    else if (text == parseInt(text)){
        console.log("INDEX");
        visibleVars = EvalTab.showOnlyIndexedItem(parseInt(text), EvalTab.varList)
    }
    else{
        visibleVars = EvalTab.showFilteredListItems(text, EvalTab.varList);
    }
    console.log(visibleVars);
    if(visibleVars.length == 1) {
        $("#eval-var-remove-btn").button("enable");
    }
    else {
        $("#eval-var-remove-btn").button("disable");
    }

    // if (text.length == 0){
    //     EvalTab.showAllListItems(EvalTab.varList);
    //     EvalTab.removeVarBtn.disabled = true;
    // }
    // else{
    //     visibleVars = EvalTab.showFilteredListItems(text, EvalTab.varList);
    //     console.log(visibleVars);
    //     if(visibleVars.length == 1) {
    //         EvalTab.removeVarBtn.disabled = false;
    //     }
    //     else {
    //         EvalTab.removeVarBtn.disabled = true;
    //     }
    // }
}

EvalTab.collectVarData = function(){
    this.data.variables = [];
    for(var child in this.varList.children){
        if (this.varList.children[child].tagName == "LI"){
            var vdata = this.collectSingleVarData(this.varList.children[child]);
            this.data.variables.push(vdata);
        }
    }
}

EvalTab.collectSingleVarData = function(li){
    var vData = {
        'name': li.children[0].value.replace(/\s/g, ""),
        'type': li.children[1].value,
    }
    return vData
}

$("#eval-var-search").bind('input', function() {
    var text = $(this).val();
    EvalTab.searchVars(text);
});

EvalTab.fillVarTab = function(vars) {
    this.varList.innerHTML = "";
    for(var v in vars){
        this.addSingleVarTab(vars[v]);
    }
}

EvalTab.addSingleVarTab = function(myVar){
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

document.getElementById("eval-var-add").onclick = function(){
    EvalTab.addVarDialog.dialog("open");
}

EvalTab.addVar = function(){
    console.log("ADDED");
    var name = document.getElementById("eval-var-name").value;
    var type = document.getElementById("eval-var-type").value;
    // 'init_val': 1.5, 'name': 'x10', 'transform': 'constant'
    var newVar = {
        'type': type,
        'name': name,
    }
    EvalTab.addSingleVarTab(newVar);
    EvalTab.addVarDialog.dialog("close");
}


EvalTab.addVarDialog = $( "#eval-var-dialog" ).dialog({
  autoOpen: false,
  width: 400,
  modal: true,
  buttons: {
    "Add Variable": EvalTab.addVar,
    Cancel: function() {
      EvalTab.addVarDialog.dialog( "close" );
    }
  },
  close: function() {
    evalVarForm[ 0 ].reset();
  }
});

evalVarForm = EvalTab.addVarDialog.find( "form" ).on( "submit", function( event ) {
  event.preventDefault();
  console.log("form");
  EvalTab.addVar();
});

EvalTab.createSelector = function(options, choice){
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

EvalTab.showOnlyIndexedItem = function(index, list){
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

EvalTab.showAllListItems = function(list){
    for (var child in list.children){
        if (list.children[child].tagName == "LI"){
            list.children[child].style.display = "inline-block";
        }
    }
}

EvalTab.showFilteredListItems = function(text, list){
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

// SAVE Tab
EvalTab.saveNewModel = function(){
    ModelTab.newModelData.name = this.newModelInput.value;
    // update the parameters in newModelData
    this.updateParameters();
    // update the variables in newModelData
    this.collectVarData();
    // Send new model to MbamUI
    // check if VALID
    // if valid, send back the load-model

    // clear out the previous UI
    // EvalTab.resetAllUI();
    // // Update ModelTab.modelData = newModelData
    // ModelTab.loadJSON(JSON.parse(JSON.stringify( ModelTab.newModelData )));
    // latexModel = JSON.parse(JSON.stringify( newLatexModel ));
    // // send 'save-model' to python
    // updateModel();
    // // click on 'Model' -> 'general'
    // $("#main-model-tab").click();
    // $("#model-general-click-tab").click();

}



EvalTab.resetAllUI = function(){
    EvalTab.clear();
    GeoTab.clear();
    ModelTab.clear();
}

EvalTab.clear = function(){
    Workspace.clear();
    this.varList.innerHTML = "";
    this.UIList.innerHTML = "";
    this.newModelInput.value = "";

}

EvalTab.updateParameters = function(){
    this.collectData();
    for (var key in this.data){
        for (var p in ModelTab.newModelData.ps){
            if(ModelTab.newModelData.ps[p].name == this.data[key].theta){
                if(this.data[key].tilde == "epsilon"){
                    ModelTab.newModelData.ps.splice(parseInt(p), 1);
                }
                else{
                    ModelTab.newModelData.ps[p].name = this.data[key].tilde;
                }
            }
        }
    }
}

EvalTab.collectVarData = function(){
    ModelTab.newModelData.vs = [];
    for(var child in this.varList.children){
        if (this.varList.children[child].tagName == "LI"){
            var vdata = this.collectSingleVarData(this.varList.children[child]);
            ModelTab.newModelData.vs.push(vdata);
        }
    }
}

EvalTab.collectSingleVarData = function(li){
    var vData = {
        'name': li.children[0].value.replace(/\s/g, ""),
        'type': li.children[1].value,
    }
    return vData
}
