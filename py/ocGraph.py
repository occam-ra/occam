import re
import itertools
import igraph
from common import *

# Drawing library boilerplate

class StripDrawer(igraph.drawing.shapes.ShapeDrawer):
    names = "strip"

    @staticmethod
    def draw_path(ctx, center_x, center_y, width, height=20):
        ctx.rectangle(center_x - width/2, center_y - height/2, width, height)

    @staticmethod
    def intersection_point(center_x, center_y, source_x, source_y, width, height=20):
        delta_x, delta_y = center_x-source_x, center_y-source_y

        if delta_x == 0 and delta_y == 0:
            return center_x, center_y

        if delta_y > 0 and delta_x <= delta_y and delta_x >= -delta_y:
            # this is the top edge
            ry = center_y - height/2
            ratio = (height/2) / delta_y
            return center_x-ratio*delta_x, ry

        if delta_y < 0 and delta_x <= -delta_y and delta_x >= delta_y:
            # this is the bottom edge
            ry = center_y + height/2
            ratio = (height/2) / -delta_y
            return center_x-ratio*delta_x, ry

        if delta_x > 0 and delta_y <= delta_x and delta_y >= -delta_x:
            # this is the left edge
            rx = center_x - width/2
            ratio = (width/2) / delta_x
            return rx, center_y-ratio*delta_y

        if delta_x < 0 and delta_y <= -delta_x and delta_y >= delta_x:
            # this is the right edge
            rx = center_x + width/2
            ratio = (width/2) / -delta_x
            return rx, center_y-ratio*delta_y

        if delta_x == 0:
            if delta_y > 0:
                return center_x, center_y - height/2
            return center_x, center_y + height/2

        if delta_y == 0:
            if delta_x > 0:
                return center_x - width/2, center_y
            return center_x + width/2, center_y
    
igraph.drawing.shapes.ShapeDrawerDirectory.register(StripDrawer)

def textwidth(text, fontsize=14):
    try:
        import cairo
    except Exception, e:
        return len(str) * fontsize
    surface = cairo.SVGSurface('undefined.svg', 600, 600)
    cr = cairo.Context(surface)
    cr.select_font_face('sans-serif', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    cr.set_font_size(fontsize)
    xbearing, ybearing, width, height, xadvance, yadvance = cr.text_extents(text)
    return width

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

    # Index full names from abbreviated 
    varDict = dict(map(lambda p : (p[1],p[0]), varlist))
    varNames = varDict.keys()
    
    if hideIV:
        varNames = set([v for r in model for v in r])
    
    # For each variable, and each association, get a unique number:
    nodes = {}
    num_vertices = 0
    for i, v in enumerate(varNames):
        nodes[v] = i

    for j, v in enumerate(model):
        if allHigherOrder or len(v) > 2:
            nodes["**".join(v)] = i + j + 1
            num_vertices = i + j + 2
    
     
    # Start with an empty graph
    graph = igraph.Graph()
    graph.add_vertices(num_vertices)
    for val,node in nodes.items():
        graph.vs[node]["abbrev"] = val
        graph.vs[node]["name"] = val if "**" in val else varDict[val]
        graph.vs[node]["type"] = True if "**" in val else False

    for rel in model:
        if len(rel) == 2 and not allHigherOrder:
            graph.add_edges([(nodes[rel[0]], nodes[rel[1]])])

        else:
            comp = nodes["**".join(rel)]
            for v in rel:
                var = nodes[v]
                graph.add_edges([(comp, var)])

    # If the DV is to be hidden, eliminate the node corresponding to it.
    if dvName != "" and hideDV:
        graph.delete_vertices(nodes[dvName])
    
    # Add labels (right now, just based on the name):
    graph.vs["label"] = map(lambda s: s.replace("**", ""), graph.vs["name" if fullVarNames else "abbrev"])

    return graph

def printPlot(graph, layout, extension, filename="graph"):
    # Setup the graph plotting aesthetics.
    tys = graph.vs["type"]
    tylabs = zip(graph.vs["type"], graph.vs["label"])
    fontsize = 8
    labWidth = lambda lab : textwidth(lab,fontsize+2)
    dotsize = 5

    # Calculate node sizes.
    nodeSize = max([0 if ty else labWidth(lab) for (ty,lab) in tylabs])
    sizeFn = (lambda ty,lab : max(nodeSize, labWidth(lab))) if layout=="bipartite" else (lambda ty,lab : dotsize if ty else nodeSize) 

    visual_style = {
        "vertex_size":[sizeFn(ty, lab) for (ty,lab) in tylabs],
        "vertex_color":["lightblue" if ty else "white" for ty in tys],
        "vertex_shape":["strip" if layout == "bipartite" and ty else "circle" for ty in tys],
        "vertex_label_size": [0 if layout!="bipartite" and ty else fontsize for ty in tys],
        "margin":max([sizeFn(ty,lab)/2 for (ty,lab) in tylabs]+[nodeSize]),

        "vertex_label_dist": 0,
        "bbox":(500, 500),
        
    }


    # Set the layout. None is a valid choice.
    layoutChoice = None
    if layout == "Fruchterman-Reingold":
        layoutChoice = graph.layout("fr")
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
    graphFile = printPlot(graph, layout, "pdf", filename=filename)
    return graphFile

def printGephi(graph):
    return "GEPHI CODE"

def printR(graph):
    return "R CODE"
