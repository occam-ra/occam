import re
import itertools
import igraph

# Graph generation based on Teresa Schmidt's R script (2016)
def generate(modelName, varlist, hideIV, hideDV, dvName, fullVarNames):
    # PARAMETERS:
    # model name: the model to make a graph of
    # variable list: variables from the data not necessarily in the model
    #   (list of pairs, containing (full name, abbrev))
    
    # Clean up the model name into a list of associations:
    # Get rid of IVI and IV
    components = modelName.split(':')
    components = filter(lambda s : not (s == 'IVI' or s == 'IV'), components)
    # Split on uppercase letters
    model = map(lambda s : re.findall('[A-Z][^A-Z]*', s), components)
    


    # Set all of the names to be either the full form or abbreviated.
    varDict = dict(map(lambda p : (p[1],p[0]), varlist))
    workingModel = [[(varDict[v] if fullVarNames else v) for v in r] for r in model]
    workingNames = set(map(lambda v : v[0 if fullVarNames else 1], varlist))
    
    if hideIV:
        workingNames = set([v for r in workingModel for v in r])

    # For each variable, and each association, get a unique number:
    workingNodes = {}
    for i, v in enumerate(workingNames):
        workingNodes[v] = i
    for j, v in enumerate(workingModel):
        workingNodes["**".join(v)] = i + j + 1

    # Start with an empty graph
    workingGraph = igraph.Graph()
    workingGraph.add_vertices(i+j+2)
    for val,node in workingNodes.items():
        workingGraph.vs[node]["name"] = val


    # if allHigherOrder were set to true,
    # dyadic relations would get a hyperedge instead of normal edge,
    # like a -- ab -- b, instead of simply a -- b
    allHigherOrder = False
    for rel in workingModel:
        if len(rel) == 2 and not allHigherOrder:
            workingGraph.add_edges([(workingNodes[rel[0]], workingNodes[rel[1]])])

        else:
            comp = workingNodes["**".join(rel)]
            for v in rel:
                var = workingNodes[v]
                workingGraph.add_edges([(comp, var)])

    # If the DV is to be hidden, eliminate the node corresponding to it.
    if hideDV:
        workingGraph.delete_vertices(workingNodes[dvName])

    return workingGraph

def printSVG(graph, layout):
    print "<br>"
    print layout
    print graph
    # constants borrowed from Teresa's script; we may want to make these options
    # vertex color = medium aquamarine
    # vertex size  = 10
    # vertex label = 0.8
    # hyperedge color   = red4
    # hyperedge size    = 2
    # hyperedge label size = 0.01


def printPDF(filename, graph):
    pass

def printGephi(graph):
    return "GEPHI CODE"

def printR(graph):
    return "R CODE"
