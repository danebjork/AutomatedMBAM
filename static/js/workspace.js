
var Workspace = {}
Workspace.space = document.getElementById("workspace");
Workspace.latex = document.getElementById("latex-space");
Workspace.moves = [];

var testEqs = {
    "math":{
        "IC": {"substitutions": ["s + u", "b - s"], "equations": ["d", "r / d"]},
        "OBS": {"substitutions": ["o - b", "s + v"], "equations": ["o", "b / s"]},
        "RHS": {"substitutions": ["r + h", "s - r"], "equations": ["r", "h / s"]},
        "INPUT": {"substitutions": ["i + n", "p - u"], "equations": ["t", "s / e"]},
    },
    "latex":{
        "IC": {"substitutions": ["s + u", "b - s"], "equations": ["d", "\\frac{r}{d}"]},
        "OBS": {"substitutions": ["o - b", "s + v"], "equations": ["o", "\\frac{b}{s}"]},
        "RHS": {"substitutions": ["r + h", "s - r"], "equations": ["r", "\\frac{h}{s}"]},
        "INPUT": {"substitutions": ["i + n", "p - u"], "equations": ["t", "\\frac{s}{e}"]},
    }
}

Workspace.FunctionButtonList = [
    "model-general-tab",
    "model-data-tab",
    "model-parameters-tab",
    "model-variables-tab",
    "model-julia-tab",
    "model-save-tab",
];

Workspace.ODEButtonList = [
    "eval-add-ic-btn",
    "eval-add-rhs-btn",
    "eval-add-obs-btn",
    "eval-add-input-btn",
    "eval-export-ic-btn",
    "eval-export-rhs-btn",
    "eval-export-obs-btn",
    "eval-export-input-btn"
];

Workspace.allEqButtons = [
    "eval-add-ic-btn",
    "eval-add-rhs-btn",
    "eval-add-obs-btn",
    "eval-add-input-btn",
    "eval-export-ic-btn",
    "eval-export-rhs-btn",
    "eval-export-obs-btn",
    "eval-export-input-btn",
    "eval-add-icd-btn",
    "eval-add-res-btn",
    "eval-export-icd-btn",
    "eval-export-res-btn",
];

Workspace.DAEButtonList = [
    "eval-add-ic-btn",
    "eval-add-icd-btn",
    "eval-add-res-btn",
    "eval-add-obs-btn",
    "eval-add-input-btn",
    "eval-export-ic-btn",
    "eval-export-icd-btn",
    "eval-export-res-btn",
    "eval-export-obs-btn",
    "eval-export-input-btn"
];

Workspace.showButtons = function(model_type){
    var eqBtns = []
    if (model_type.toLowerCase() == "ode"){
        eqBtns = Workspace.ODEButtonList
    }
    else if (model_type.toLowerCase() == "dae"){
        eqBtns = Workspace.DAEButtonList
    }
    for(var b in Workspace.allEqButtons){
        button_id = Workspace.allEqButtons[b]
        button = document.getElementById(button_id)
        if (eqBtns.indexOf(button_id) == -1){
            button.style.display = "none";
        }
        else{
            button.style.display = "inline-block";
        }
    }
}

document.getElementById("eval-add-ic-btn").onclick = function(){
    Workspace.dialogType = "ic";
    Workspace.addEqsDialog.dialog("open");
}

document.getElementById("eval-add-icd-btn").onclick = function(){
    Workspace.dialogType = "icd";
    Workspace.addEqsDialog.dialog("open");
}

document.getElementById("eval-add-rhs-btn").onclick = function(){
    Workspace.dialogType = "rhs";
    Workspace.addEqsDialog.dialog("open");
}

document.getElementById("eval-add-res-btn").onclick = function(){
    Workspace.dialogType = "res";
    Workspace.addEqsDialog.dialog("open");
}

document.getElementById("eval-add-obs-btn").onclick = function(){
    Workspace.dialogType = "obs";
    Workspace.addEqsDialog.dialog("open");
}

document.getElementById("eval-add-input-btn").onclick = function(){
    Workspace.dialogType = "inp";
    Workspace.addEqsDialog.dialog("open");
}

// export equations buttons
document.getElementById("eval-export-ic-btn").onclick = function(){
    Workspace.dialogType = "ic";
    Workspace.exportEqsDialog.dialog("open");
}

document.getElementById("eval-export-rhs-btn").onclick = function(){
    Workspace.dialogType = "rhs";
    Workspace.exportEqsDialog.dialog("open");
}

document.getElementById("eval-export-obs-btn").onclick = function(){
    Workspace.dialogType = "obs";
    Workspace.exportEqsDialog.dialog("open");
}

document.getElementById("eval-export-input-btn").onclick = function(){
    Workspace.dialogType = "inp";
    Workspace.exportEqsDialog.dialog("open");
}

Workspace.exportEqs = function(add){
    console.log("Exported!");
    var lis = Workspace.subExportDialogList.children;
    for(var i in lis){
        if(lis[i].clicked){
            newLatexModel[Workspace.dialogType].sbs[i] = Workspace.latex.children[2].innerText;
            ModelTab.newModelData[Workspace.dialogType].sbs[i] = Workspace.getText();
        }
    }
    var lis = Workspace.eqExportDialogList.children;
    for(var i in lis){
        if(lis[i].clicked){
            newLatexModel[Workspace.dialogType].eqs[i] = Workspace.latex.children[2].innerText;
            ModelTab.newModelData[Workspace.dialogType].eqs[i] = Workspace.getText();
        }
    }
    Workspace.exportEqsDialog.dialog( "close" );
}


Workspace.addEqs = function(){
    console.log("ADDED");
    var lis = Workspace.subAddDialogList.children;
    for(var i in lis){
        if(lis[i].clicked){
            Workspace.space.value += "\n + (" + lis[i].id +")";
        }
    }
    var lis = Workspace.eqAddDialogList.children;
    for(var i in lis){
        if(lis[i].clicked){
            Workspace.space.value += "\n + (" + lis[i].id +")";
        }
    }
    Workspace.addEqsDialog.dialog( "close" );
}

Workspace.displayEqInDialog = function(type, add){
    this.clearEqDialog()
    this.loadEqType(type, add);
    MathJax.Hub.Typeset();
}

Workspace.subAddDialogList = document.getElementById("eval-add-dialog-subs");
Workspace.eqAddDialogList = document.getElementById("eval-add-dialog-eqs");

Workspace.subExportDialogList = document.getElementById("eval-export-dialog-subs");
Workspace.eqExportDialogList = document.getElementById("eval-export-dialog-eqs");

Workspace.loadEqType = function(type, add){
    for(var sub in latexModel[type].sbs){
        console.log(latexModel[type].sbs[sub]);
        if (add){
            var li = Workspace.createEqLI(sub, latexModel[type].sbs[sub], ModelTab.modelData[type].sbs[sub]);
            this.subAddDialogList.appendChild(li);
        }
        else{
            var li = Workspace.createEqLI(sub, newLatexModel[type].sbs[sub], ModelTab.newModelData[type].sbs[sub]);
            this.subExportDialogList.appendChild(li);
        }

    }
    for(var eq in latexModel[type].eqs){
        if (add){
            Workspace.createEqLI(eq, latexModel[type].eqs[eq], type);
            var li = Workspace.createEqLI(eq, latexModel[type].eqs[eq], ModelTab.modelData[type].eqs[eq]);
            this.eqAddDialogList.appendChild(li);
        }
        else{
            Workspace.createEqLI(sub, newLatexModel[type].eqs[eq], type);
            var li = Workspace.createEqLI(eq, newLatexModel[type].eqs[eq], ModelTab.newModelData[type].eqs[eq]);
            this.eqExportDialogList.appendChild(li);
        }

    }
}

Workspace.findBackgroundColor = function(clicked){
    if (clicked) {
        return "#fffc0066";
    }
    return "#ffffff";
}

Workspace.clearEqDialog = function(){
    this.subAddDialogList.innerHTML = "";
    this.eqAddDialogList.innerHTML = "";
    this.subExportDialogList.innerHTML = "";
    this.eqExportDialogList.innerHTML = "";
}

Workspace.createEqLI = function(index, latex, python) {
    var node = document.createElement("LI");
    if (python.indexOf("=") != -1){
        node.id = python.split("=")[1];
    }
    else{
        node.id = python;
    }
    var textnode = document.createTextNode("$$" + latex + "$$");
    node.appendChild(textnode);
    node.onclick = function(){
        this.clicked = !this.clicked;
        this.style.backgroundColor =  Equations.findBackgroundColor(this.clicked);
    }
    node.onmouseover = function() {
        this.style.backgroundColor = "#73f2fc";
    }
    node.onmouseout = function() {
        this.style.backgroundColor =  Equations.findBackgroundColor(this.clicked);
    }
    node.style.marginTop = "10pt";
    return node
}

Workspace.exportEqsDialog = $( "#eval-export-eq-dialog" ).dialog({
  autoOpen: false,
  modal: true,
  height: 650,
  width: 900,
  buttons: {
    "Export Eqautions": Workspace.exportEqs,
    Cancel: function() {
      Workspace.exportEqsDialog.dialog( "close" );
    }
  },
  open: function(){
      Workspace.displayEqInDialog(Workspace.dialogType, false);
  },
  close: function() {
    exportEqForm[ 0 ].reset();
  }
});

exportEqForm = Workspace.exportEqsDialog.find( "form" ).on( "submit", function( event ) {
  event.preventDefault();
  Workspace.exportEqs();
});

Workspace.addEqsDialog = $( "#eval-eq-dialog" ).dialog({
  autoOpen: false,
  modal: true,
  height: 650,
  width: 900,
  buttons: {
    "Add Eqautions": Workspace.addEqs,
    Cancel: function() {
      Workspace.addEqsDialog.dialog( "close" );
    }
  },
  open: function(){
      Workspace.displayEqInDialog(Workspace.dialogType, true);
  },
  close: function() {
      console.log("reset")
    addEqForm[ 0 ].reset();
  }
});

addEqForm = Workspace.addEqsDialog.find( "form" ).on( "submit", function( event ) {
  event.preventDefault();
  console.log("ADD EQ");
  Workspace.addEqs();
});


Workspace.getText = function() {
    return this.space.value;
}
Workspace.setText = function(text) {
    this.space.value = text;
}

Workspace.undo = function() {
    if(this.moves.length != 0){
        this.setText(this.moves.pop());
    }
}

Workspace.send = function(websocket, command) {
    websocket.send(command);
}

Workspace.simplify = function(websocket){
    send = {"type": "simplify", "eq": this.space.value};
    this.send(websocket, JSON.stringify(send));
}

Workspace.simplifyCallback = function(data) {
    this.setText(data.eq);
    this.setLatex(data.latex);
}

Workspace.substitute = function(data) {
    this.moves.push(Workspace.getText());
    this.setText(data.eq);
    this.setLatex(data.latex);
}

Workspace.epsilon = function(websocket){
    this.moves.push(Workspace.getText());
    send = {"type": "epsilon", "eq": this.space.value};
    this.send(websocket, JSON.stringify(send));
}

Workspace.epsilonCallback = function(data) {
    console.log("EPSILON");
    this.setText(data.eq);
    this.setLatex(data.latex);
}

Workspace.setLatex = function(eq) {
    this.latex.innerHTML = "$$" + eq + "$$";
    MathJax.Hub.Typeset();
}

Workspace.clear = function(){
    this.setLatex("");
    Workspace.space.value = "";
}

// testing
// Workspace.setText("((1/((-epsilon + 1/theta1)*(theta1/theta2 - theta12)))*((-epsilon + 1/theta1)*(theta1/theta2 - theta12)))*(-x/(epsilon*(x + 1/(epsilon*theta12))))");
// Workspace.setText("(-theta_1*x) / (theta_2 + x)");
