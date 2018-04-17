var Equations = {};

Equations.selected = [];

Equations.load = function(priority, latex_eq) {
    this.priority = document.getElementById("priority-eqs");
    this.nonpriority = document.getElementById("non-priority-eqs");
    this.priority.innerHTML = "";
    this.nonpriority.innerHTML = "";
    this.listEquations(priority.sub, latex_eq.sub, 'sub');
    this.listEquations(priority.eq, latex_eq.sub_eq, 'eq');
    // Add "Add equations Button" to put equations in workspace and close window
}

// Start with an initial array
var array = ["a", "b", "c"];

// Find and remove item from an array
var i = array.indexOf("b");
if(i != -1) {
	array.splice(i, 1);
}


Equations.listEquations = function(priority, eqs, type){
    for (var key in eqs){
        var node = this.createEqLI(key, eqs[key], type);
        if (key in priority) {
            this.priority.appendChild(node);
        }
        else {
            this.nonpriority.appendChild(node);
        }
    }
}

Equations.createEqLI = function(index, eq, type) {
    var node = document.createElement("LI");
    node.id = "type-" + index;
    var textnode = document.createTextNode("$$" + eq + "$$");
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

Equations.findBackgroundColor = function(clicked){
    if (clicked) {
        return "#fffc0066";
    }
    return "#ffffff";
}


Equations.close = function() {
    this.window.close();
}
