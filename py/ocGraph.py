import re
import itertools
import igraph
from common import *

# Graph generation based on Teresa Schmidt's R script (2016)
def generate(modelName, varlist, hideIV, hideDV, dvName, fullVarNames, allHigherOrder):
    # PARAMETERS:
    # model name: the model to make a graph of
    # variable list: variables from the data not necessarily in the model
    #   (list of pairs, containing (full name, abbrev))
    # if allHigherOrder were set to true,
    # dyadic relations would get a hyperedge instead of normal edge,
    # like a -- ab -- b, instead of simply a -- b
    
    # Clean up the model name into a list of associations:
    # Get rid of IVI and IV
    components = modelName.split(':')
    components = filter(lambda s : not (s == 'IVI' or s == 'IV'), components)
    # Split on uppercase letters
    model = map(lambda s : re.findall('[A-Z][^A-Z]*', s), components)
    if dvName != "":
        model = filter(lambda r : dvName in r, model)

    # Set all of the names to be either the full form or abbreviated.
    varDict = dict(map(lambda p : (p[1],p[0]), varlist))
    fullDvName = varDict[dvName]
    workingModel = [[(varDict[v] if fullVarNames else v) for v in r] for r in model]
    workingNames = set(map(lambda v : v[0 if fullVarNames else 1], varlist))
    
    if hideIV:
        workingNames = set([v for r in workingModel for v in r])

    
    # For each variable, and each association, get a unique number:
    workingNodes = {}
    num_vertices = 0
    for i, v in enumerate(workingNames):
        workingNodes[v] = i
    for j, v in enumerate(workingModel):
        if allHigherOrder or len(v) > 2:
            workingNodes["**".join(v)] = i + j + 1
            num_vertices = i + j + 2
    
    
    # Start with an empty graph
    workingGraph = igraph.Graph()
    workingGraph.add_vertices(num_vertices)
    for val,node in workingNodes.items():
        workingGraph.vs[node]["name"] = val
        workingGraph.vs[node]["type"] = True if "**" in val else False


    for rel in workingModel:
        if len(rel) == 2 and not allHigherOrder:
            workingGraph.add_edges([(workingNodes[rel[0]], workingNodes[rel[1]])])

        else:
            comp = workingNodes["**".join(rel)]
            for v in rel:
                var = workingNodes[v]
                workingGraph.add_edges([(comp, var)])

    # If the DV is to be hidden, eliminate the node corresponding to it.
    if dvName != "" and hideDV:
        workingGraph.delete_vertices(workingNodes[fullDvName if fullVarNames else dvName])
    
    # Add labels (right now, just based on the name):
    workingGraph.vs["label"] = map(lambda s: s.replace("**", " - " if fullVarNames else ""), workingGraph.vs["name"])

    return workingGraph


def printPlot(graph, layout, extension, filename="graph"):
    # Setup the graph plotting aesthetics.
    # constants borrowed from Teresa's script; we may want to make these options
    color_dict = {True: "lightblue", False: "white"}
    shape_dict = {True: "circle", False: "hidden"}
    visual_style = {
        "vertex_size":20,
        "vertex_color":[color_dict[ty] for ty in graph.vs["type"]],
        "margin":100,
        "vertex_shape":[shape_dict[ty] for ty in graph.vs["type"]],
        
    }
# vertex color = medium aquamarine
    # vertex size  = 10
    # vertex label = 0.8
    # hyperedge color   = red4
    # hyperedge size    = 2
    # hyperedge label size = 0.01


    # Set the layout. None is a valid choice.
    layoutChoice = None
    if layout == "Fruchterman-Reingold":
        layoutChoice = graph.layout("fr")
    elif layout == "DrL":
        layoutChoice = graph.layout("drl")
    elif layout == "bipartite":
        layoutChoice = graph.layout("bipartite")
    elif layout == "Reingold-Tilford":
        layoutChoice = graph.layout("rt")

    # Generate a unique file for the graph;
    # using the layout (if any), generate a plot.
    graphFile = getUniqueFilename(filename+"."+extension)
    igraph.plot(graph, graphFile, layout=layoutChoice, **visual_style)
    return graphFile

def printSVG(graph, layout):
    print "<br>"
    graphFile = printPlot(graph, layout, "svg")
    with open(graphFile) as gf:
        contents = gf.read()
        print contents

def printPDF(filename, graph, layout):
    print "got to here"
    graphFile = printPlot(graph, layout, "pdf", filename=filename)
    return graphFile

def printGephi(graph):
    return "GEPHI CODE"

def printR(graph):
    return "R CODE"
