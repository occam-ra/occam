# coding=utf-8
# Copyright © 1990 The Portland State University OCCAM Project Team
# [This program is licensed under the GPL version 3 or later.]
# Please see the file LICENSE in the source
# distribution of this software for license terms.

import igraph
import re
from common import *

# Drawing library boilerplate


class StripDrawer(igraph.drawing.shapes.ShapeDrawer):
    names = "strip"

    @staticmethod
    def draw_path(ctx, center_x, center_y, width, height=20):
        ctx.rectangle(
            center_x - width / 2, center_y - height / 2, width, height
        )

    @staticmethod
    def intersection_point(
        center_x, center_y, source_x, source_y, width, height=20
    ):
        delta_x, delta_y = center_x - source_x, center_y - source_y

        if delta_x == 0 and delta_y == 0:
            return center_x, center_y

        if delta_y > 0 and delta_y >= delta_x >= -delta_y:
            # this is the top edge
            ry = center_y - height / 2
            ratio = (height / 2) / delta_y
            return center_x - ratio * delta_x, ry

        if delta_y < 0 and -delta_y >= delta_x >= delta_y:
            # this is the bottom edge
            ry = center_y + height / 2
            ratio = (height / 2) / -delta_y
            return center_x - ratio * delta_x, ry

        if delta_x > 0 and delta_x >= delta_y >= -delta_x:
            # this is the left edge
            rx = center_x - width / 2
            ratio = (width / 2) / delta_x
            return rx, center_y - ratio * delta_y

        if delta_x < 0 and -delta_x >= delta_y >= delta_x:
            # this is the right edge
            rx = center_x + width / 2
            ratio = (width / 2) / -delta_x
            return rx, center_y - ratio * delta_y

        if delta_x == 0:
            if delta_y > 0:
                return center_x, center_y - height / 2
            return center_x, center_y + height / 2

        if delta_y == 0:
            if delta_x > 0:
                return center_x - width / 2, center_y
            return center_x + width / 2, center_y


igraph.drawing.shapes.ShapeDrawerDirectory.register(StripDrawer)


def textwidth(text, fontsize=14):
    try:
        import cairo
    except Exception:
        return len(text) * fontsize
    surface = cairo.SVGSurface('data/undefined.svg', 600, 600)
    cr = cairo.Context(surface)
    cr.select_font_face(
        'sans-serif', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD
    )
    cr.set_font_size(fontsize)
    x_bearing, y_bearing, width, height, x_advance, y_advance = cr.text_extents(
        text
    )
    return width


# Graph generation based on Teresa Schmidt's R script (2016)
def generate(
    model_name,
    varlist,
    hide_iv,
    hide_dv,
    dv_name,
    full_var_names,
    all_higher_order,
):

    # TODO fix this... the split is not quite working out right.

    # PARAMETERS:
    # model name: the model to make a graph of
    # variable list: variables from the data not necessarily in the model
    #   (list of pairs, containing (full name, abbrev))
    # if all_higher_order were set to true,
    # dyadic relations would get a hyperedge instead of normal edge,
    # like a -- ab -- b, instead of simply a -- b

    # Clean up the model name into a list of associations:
    # Get rid of IVI and IV
    components = model_name.split(':')
    components = [s for s in components if not (s == 'IVI' or s == 'IV')]
    # Split on uppercase letters
    model = [re.findall('[A-Z][^A-Z]*', s) for s in components]
    if dv_name != "":
        model = [r for r in model if dv_name in r]

    # Index full names from abbreviated
    var_dict = {p[1]: p[0] for p in varlist}
    var_names = list(var_dict.keys())

    if hide_iv:
        var_names = {v for r in model for v in r}

        if not components:
            return igraph.Graph()

    # For each variable, and each association, get a unique number:
    nodes = {}
    num_nodes = len(var_names)
    num_edges = 0

    for i, v in enumerate(var_names):
        nodes[v] = i

    for j, v in enumerate(model):
        if all_higher_order or len(v) > 2:
            nodes["**".join(v)] = num_nodes + num_edges
            num_edges += 1

    num_vertices = num_nodes + num_edges

    # Start with an empty graph
    graph = igraph.Graph()
    graph.add_vertices(num_vertices)
    for val, node in list(nodes.items()):
        graph.vs[node]["id"] = val
        short = val.replace("**", "")
        graph.vs[node]["abbrev"] = short
        graph.vs[node]["name"] = short if "**" in val else var_dict[val]
        graph.vs[node]["type"] = True if "**" in val else False

    for rel in model:
        if len(rel) == 2 and not all_higher_order:
            graph.add_edges([(nodes[rel[0]], nodes[rel[1]])])
        else:
            comp = nodes["**".join(rel)]
            for v in rel:
                var = nodes[v]
                graph.add_edges([(comp, var)])

    # If the DV is to be hidden, eliminate the node corresponding to it.
    if dv_name != "" and hide_dv:
        graph.delete_vertices(nodes[dv_name])

    # Add labels (right now, just based on the name):
    graph.vs["label"] = graph.vs["name" if full_var_names else "abbrev"]
    return graph


def print_plot(
    graph,
    layout,
    extension,
    filename,
    width,
    height,
    font_size,
    node_size_orig,
):
    # Setup the graph plotting aesthetics.
    tys = graph.vs["type"]
    tylabs = list(zip(graph.vs["type"], graph.vs["label"]))
    fontsize = font_size
    lab_width = lambda lab: textwidth(lab, fontsize * 1.5)
    dotsize = 5

    # Calculate node sizes.
    node_size = max(
        [
            0 if ty else max(node_size_orig, lab_width(lab))
            for (ty, lab) in tylabs
        ]
    )
    size_fn = (
        (lambda ty, lab: max(node_size, lab_width(lab)))
        if layout == "bipartite"
        else (lambda ty, lab: dotsize if ty else node_size)
    )

    visual_style = {
        "vertex_size": [size_fn(ty, lab) for (ty, lab) in tylabs],
        "vertex_color": ["lightblue" if ty else "white" for ty in tys],
        "vertex_shape": [
            "strip" if layout == "bipartite" and ty else "circle" for ty in tys
        ],
        "vertex_label_size": [
            0 if layout != "bipartite" and ty else fontsize for ty in tys
        ],
        "margin": max(
            [size_fn(ty, lab) / 2 for (ty, lab) in tylabs] + [node_size]
        ),
        "vertex_label_dist": 0,
        "bbox": (width, height),
    }

    # Set the layout. None is a valid choice.
    layout_choice = None

    try:
        if layout == "Fruchterman-Reingold":
            layout_choice = graph.layout("fr")
        elif layout == "bipartite":
            layout_choice = graph.layout_as_bipartite()
        elif layout == "Reingold-Tilford":
            layout_choice = graph.layout("rt")
        elif layout == "Graph_opt":
            layout_choice = "graphopt"
        elif layout == "Kamada-Kawai":
            layout_choice = "kk"
        elif layout == "Sugiyama":
            layout_choice = "sugiyama"
    except Exception:
        raise RuntimeError(
            f"The hypergraph layout library failed to apply the {layout} layout."
        )

    # Generate a unique file for the graph;
    # using the layout (if any), generate a plot.
    graph_file = get_unique_filename(f"data/{filename}.{extension}")
    igraph.plot(graph, graph_file, layout=layout_choice, **visual_style)
    return graph_file


def print_svg(graph, layout, width, height, font_size, node_size):
    print("<br>")
    graph_file = print_plot(
        graph, layout, "svg", "graph", width, height, font_size, node_size
    )
    with open(graph_file) as gf:
        contents = gf.read()
        print(contents)


def print_pdf(filename, graph, layout, width, height, font_size, node_size):
    graph_file = print_plot(
        graph, layout, "pdf", filename, width, height, font_size, node_size
    )
    return graph_file


def print_gephi(graph):

    nl_header = "<br><br><i>Gephi 'Nodes table' file:</i><pre><code>"
    nl_footer = "</code></pre>"
    el_header = "<br><br><i>Gephi 'Edges table' file:</i><pre><code>"
    el_footer = "</code></pre>"

    nl = gephi_nodes(graph)
    el = gephi_edges(graph)

    gephi_code = nl_header + nl + nl_footer + el_header + el + el_footer
    return gephi_code


def gephi_nodes(graph):
    header = "ID,Label,Type,Size\n"
    content = ""
    for n in graph.vs:
        ty = "Hyper_edge" if n["type"] else "Variable"
        size = 4 if n["type"] else 10
        line = ",".join([n["abbrev"], n["name"], ty, str(size)])
        content += f"{line}\n"
    return header + content


def gephi_edges(graph):
    header = "Source,Target\n"
    content = ""
    for n1, n2 in graph.get_edgelist():
        nn1 = graph.vs[n1]
        nn2 = graph.vs[n2]
        content += f"{nn1['abbrev']},{nn2['abbrev']}\n"

    return header + content
