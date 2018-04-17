var GeoGraphs = {}


GeoGraphs.initVals = function(){
    // initialize variables for plots
    GeoGraphs.plotDivs = [];
    GeoGraphs.layouts = [];
    GeoGraphs.initTraces();
}

GeoGraphs.initTraces = function(){
    // A list of all plotted parameters (Used to prevent duplicates)
    GeoGraphs.plottedParams = [];
    // traces for upper left plot
    GeoGraphs.traces1 = [];
    // traces for upper right plot
    GeoGraphs.traces2 = [];
    // data for the bar plot
    GeoGraphs.barTraces = [];
}



GeoGraphs.initVals();

GeoGraphs.update = function(data) {
    this.updateLeftPlot(data.x);
    this.updateRightPlot(data.x, data.t, data.tau);
    this.updateBar(data.v)
}

GeoGraphs.transpose = function(array) {
    var newArray = array[0].map(function(col, i) {
        return array.map(function(row) {
            return row[i]
        })
    });
    return newArray;
}

GeoGraphs.updateLeftPlot = function(xs) {
    // xs = this.transpose(xs);
    this.traces1[0].x = xs[0];
    this.traces1[0].y = xs[1];
    Plotly.redraw(this.plotDivs[0]);
}

GeoGraphs.updateRightPlot = function(xs, ts, taus) {
    // xs = this.transpose(xs);
    // ts = this.transpose(ts)[0];
    // taus = this.transpose(taus)[0];
    for(var key in this.traces2) {
        this.traces2[key].y = xs[key];
        this.traces2[key].x = ts;
    }
    Plotly.redraw(this.plotDivs[1]);
}

GeoGraphs.updateBar = function(vel) {
    var recent = vel[vel.length - 1];
    for(var v = 0; v < recent.length; v++) {
        this.barTraces[v]['y'] = [recent[v]];
    }
    Plotly.redraw(this.plotDivs[2]);
}

GeoGraphs.init = function(){
    GeoGraphs.plotDivs = [];
    GeoGraphs.layouts = [];
    // get the plot divs
    this.plotDivs.push(document.getElementById('plot-one'));
    this.plotDivs.push(document.getElementById('plot-two'));
    this.plotDivs.push(document.getElementById('plot-three'));
    // add the layouts
    this.layouts.push({
        hovermode:'closest',
        title:"VS Plot",
        yaxis:{
            title:"p[1]",
        },
        xaxis:{
            title:"p[2]",
        },
    });
    this.layouts.push({
        hovermode:'closest',
        title:"Parameters",
        yaxis:{
            title:"Parameter",
        },
        xaxis:{
            title:"Time",
        },
    });
    this.layouts.push({
       hovermode:'closest',
       title:"Parameter Velocities",
       yaxis:{title:"Velocity"},
     });

    Plotly.plot(this.plotDivs[0], this.traces1, this.layouts[0], {displaylogo: false, editable: true});
    Plotly.plot(this.plotDivs[1], this.traces2, this.layouts[1], {displaylogo: false, editable: true});
    Plotly.plot(this.plotDivs[2], this.barTraces, this.layouts[2], {displaylogo: false});
}

GeoGraphs.clear = function(){
    Plotly.purge(GeoGraphs.plotDivs[0]);
    Plotly.purge(GeoGraphs.plotDivs[1]);
    Plotly.purge(GeoGraphs.plotDivs[2]);
    GeoGraphs.initVals();
    GeoGraphs.init();
}

GeoGraphs.resizePlots = function() {
    for(var key in this.plotDivs) {
        Plotly.Plots.resize(this.plotDivs[key]);
        Plotly.Plots.resize(this.plotDivs[key]);
    }
}

GeoGraphs.format = function(params){
    // this.initVals();
    // initialize trace in left plot
    if(params.length > 1) {
        var label = "" + params[0].name + " vs " + params[1].name;
        this.traces1.push({	x: [],	y: [] , name: label});
    }
    // initialize traces in right plot and bar graphs
    for(var p in params) {
        if(params[p].transform != "constant") {
            var label = params[p].name;
            if(this.plottedParams.indexOf(label) == -1) {
                this.barTraces.push({x:["Parameters"], y:[], type:"bar", name: label});
                this.traces2.push({x: [], y: [], name: label});
                this.plottedParams.push(label);
            }
        }
    }
}
