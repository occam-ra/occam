
polygonExample = """
<?xml version="1.0" encoding="UTF-8" standalone="no"?>

<svg xmlns="http://www.w3.org/2000/svg" version="1.0" width="480" height="543.03003" viewBox="0 0 257.002 297.5" xml:space="preserve">

<g transform="matrix(0.8526811,0,0,0.8526811,18.930632,21.913299)">

<polygon points="8.003,218.496 0,222.998 0,74.497 8.003,78.999 8.003,218.496 "/>

<polygon points="128.501,287.998 128.501,297.5 0,222.998 8.003,218.496 128.501,287.998 " />

<polygon points="249.004,218.496 257.002,222.998 128.501,297.5 128.501,287.998 249.004,218.496 " />

<polygon points="249.004,78.999 257.002,74.497 257.002,222.998 249.004,218.496 249.004,78.999 " />

<polygon points="128.501,9.497 128.501,0 257.002,74.497 249.004,78.999 128.501,9.497 " />

<polygon points="8.003,78.999 0,74.497 128.501,0 128.501,9.497 8.003,78.999 " />

</g>

</svg>

"""

# Graph generation based on Teresa Schmidt's R script (2016)
def generate(modelName, varlist, layout, hideIV, hideDV, fullVarNames):
    # PARAMETERS:
    # model name: the model to make a graph of
    # variable list: variables from the data not necessarily in the model
    #   (list of pairs, containing (full name, abbrev))

    print "GRAPH:"
    print modelName
    print varlist
    print layout
    print hideIV
    print hideDV
    print fullVarNames
    

    # constants borrowed from Teresa's script; we may want to make these options
    # vertex color = medium aquamarine
    # vertex size  = 10
    # vertex label = 0.8
    # hyperedge color   = red4
    # hyperedge size    = 2
    # hyperedge label size = 0.01


    # TO MAKE A GRAPH:

    # Clean up the model name into a list of associations:
    # Get rid of IVI and IV
    # Split on Colon
    # Split on uppercase letters
    # Annotate each association with its order, i.e. 2-way, 3-way, ...
    
    # Optionally, make a node for each variable.
    # Otherwise, add nodes as they are needed in edges.

    # Make simple edges for each 2-way association:
        # Filter out the 2-way associations
        # Add an edge pair for each one.
        # Optionally, disable this and treat it as higher-order.
    
    # Make hyperedges for each higher-order association:
        # Give each higher-order association a new node.
        # Make a 2-way association between variables and association nodes,
        # for the associations the variable is contained in,
        # i.e. a bipartite graph.

    # Combine the edge lists into a single list of edges.

    # Package the graph up for IGRAPH:



    
    
    return ""

def printSVG(graph):
    print polygonExample
    print "<br>"


def printPDF(filename, graph):
    pass

def printGephi(graph):
    return "GEPHI CODE"

def printR(graph):
    return "R CODE"
