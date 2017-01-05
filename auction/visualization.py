"""Tools for creating graphical visualizations of auction algorithms."""

import re
import json
try:
    from IPython import display
except ImportError:
    pass

class AuctionGraphVisualizer(object):
    """Abstract base class for graph visualizations."""

    def draw_graph(self, graph):
        raise NotImplementedError("Subclasses must implement draw_graph.")

    def template_sub(template, **kwargs):
        """Perform string substitution into the given template. All occurrences
        of {{varname}} will be replaced with the value of the keyword argument
        varname."""

        if not kwargs:
            return template

        sub_dict = {re.escape("{{" + k + "}}"): v for k, v in kwargs.items()}
        regex = re.compile("({})".format("|".join(sub_dict.keys())))

        return regex.sub(
            lambda mo: str(sub_dict[re.escape(mo.string[mo.start():mo.end()])]),
            template)


class IPyDisplayD3(AuctionGraphVisualizer):
    """Graph visualizations for IPython/Jupyter notebooks using D3."""

    _newid = 0

    def __init__(self, eps, width=960, height=540):
        """Initialize an empty graph canvas in the IPython output area, and
        setup D3 for displaying graphs."""

        self.id = IPyDisplayD3._newid
        IPyDisplayD3._newid += 1

        self.eps = eps # TODO: Refactor this.
        self.width = width
        self.height = height

        # (Hopefully) unique element ID for the div containing the graph.
        self.div_id = "ipd3_graph_{}".format(self.id)

        display.clear_output(wait=True)

        # TODO: Move these js snippets to external files?
        output = AuctionGraphVisualizer.template_sub("""
            // Load D3 library.
            require.config({
                paths: {
                    d3: "//cdnjs.cloudflare.com/ajax/libs/d3/3.4.8/d3.min"
                }
            });

            require(["d3"], function(d3) {
                $("#{{g_div_id}}").remove();

                // Create div for canvas.
                element.append("<div id='{{g_div_id}}'></div>");
                $("#{{g_div_id}}").width("{{width}}px");
                $("#{{g_div_id}}").height("{{height}}px");

                // (Warning: ugly!) Attach svg canvas to window.
                var svg = d3.select("#{{g_div_id}}").append("svg")
                    .attr("width", {{width}})
                    .attr("height", {{height}});

                var g = {};
                window.{{g_div_id}} = g;
                g.svg = svg;

                g.defs = svg.append("svg:defs");
                g.defs.append("svg:marker")
                    .attr("id", "triangle-marker")
                    .attr("viewBox", "0 -5 10 10")
                    .attr("refX", 15)
                    .attr("refY", -1.5)
                    .attr("markerWidth", 6)
                    .attr("markerHeight", 6)
                    .attr("orient", "auto")
                    .append("path")
                    .attr("d", "M0,-5L10,0L0,5")
                    .style("fill", "hsl(194,60%,31.6%)");
            });
            """, g_div_id=self.div_id, width=self.width, height=self.height)

        display.display(display.Javascript(output))

    draw_js_tpl = """
        require(["d3"], function(d3) {
            var g = window.{{g_div_id}};
            var svg = g.svg;
            console.log(svg);

            // Clear previous canvas state (nodes/edges).
            $("#{{g_div_id}} .node, #{{g_div_id}} .link, #{{g_div_id}} .link_hov").remove();

            var nodes = {{nodes}};
            var edges = {{edges}};

            function linkArc(d) {
                var dx = nodes[d.target].x - nodes[d.source].x,
                    dy = nodes[d.target].y - nodes[d.source].y,
                    dr = Math.sqrt(dx * dx + dy * dy);
                return "M" + nodes[d.source].x + ","
                    + nodes[d.source].y + "A" + dr + "," + dr + " 0 0,1 "
                    + nodes[d.target].x + "," + nodes[d.target].y;
            }

            var link = svg.selectAll(".link")
                .data(edges)
                .enter()
                .append("path")
                .attr("class", "link")
                .attr("d", linkArc)
                .attr("marker-end", "url(#triangle-marker)")
                .style("stroke", "hsl(194,60%,31.6%)")
                .style("stroke-width", function(d) { return d.thickness; })
                .style("fill", "none");

            var link_hov = svg.selectAll(".link_hov")
                .data(edges)
                .enter()
                .append("path")
                .attr("class", "link_hov")
                .attr("d", linkArc)
                .style("stroke", "rgba(0, 0, 0, 0)")
                .style("stroke-width", "5px")
                .style("fill", "none");

            svg.selectAll("circle .node")
                .data(d3.values(nodes))
                .enter()
                .append("svg:circle")
                .attr("class", "node")
                .attr("cx", function(d) { return d.x })
                .attr("cy", function(d) { return d.y })
                .attr("r", "5px")
                .attr("fill", function(d) { return d.color });

            $("#{{g_div_id}} svg").tooltip({
                items: ".node,.link_hov",
                content: function() {
                    return this.__data__.tooltip;
                },
                track: true,
                show: false,
                hide: false
            });
        });
        """

    def draw_graph(self, graph):
        # TODO: Instead of redrawing the entire graph each time, keep track of
        # data and update it as needed.

        nodes = {id(node): {
                "x": node.x_pos,
                "y": node.y_pos,
                "label": node.label,
                "tooltip": node.html,
                # TODO: Make smarter policy for node coloring.
                "color": "hsl(7," + str(100 * min(1, node.price / 1)) + "%,42.28%)"
            } for node in graph.nodes}

        edges = [
            {
                "source": id(edge.source),
                "target": id(edge.target),
                "tooltip": edge.html(self.eps),
                "thickness": str(2 * edge.flow / (edge.capacity if edge.capacity is not None else 1)) + "px" # TODO:
            } for edge in graph.edges if edge.flow > 0]

        output = AuctionGraphVisualizer.template_sub(
            IPyDisplayD3.draw_js_tpl,
            g_div_id=self.div_id, nodes=json.dumps(nodes), edges=json.dumps(edges))

        display.display(display.Javascript(output))

