"""Representation of graphs/flow networks for auction algorithms."""


class Graph(object):
    """
    A graph, or flow network, for running and visualizing auction algorithms.
    """

    def __init__(self, nodes=None):
        self.nodes = set(nodes) if nodes is not None else set()
        # TODO: Keep track of nodes with positive surplus.

        # Construct this graph's set of edges. Note that this assumes that all
        # edges were added using the add_edge method of some graph. In
        # particular, it is assumed that every edge appears on some node's
        # out_edge list.
        self.edges = set()
        for node in self.nodes:
            self.edges.update(node.out_edges)

    def add_node(self, node):
        """
        Insert the given node into the graph.
        """
        self.nodes.add(node)

    def remove_node(self, node):
        """
        Remove the given node from the graph.
        """
        self.nodes.remove(node)

    def add_edge(self, source, target, cost=0.0, capacity=None, min_flow=0.0,
                 flow=0.0):
        """
        Create an edge and add it to the graph with the specified source and target
        nodes, and (optional) flow value, updating the corresponding node
        objects as well.
        """
        edge = Edge(source=source, target=target, cost=cost, capacity=capacity,
                    min_flow=min_flow, flow=flow)
        source.out_edges.add(edge)
        target.in_edges.add(edge)
        self.edges.add(edge)

    def remove_edge(self, edge):
        """
        Remove the given edge from the graph, as well as the nodes to which it
        is incident.
        """
        self.edges.remove(edge)
        edge.target.in_edges.remove(edge)


class Node(object):
    def __init__(self, label="", x_pos=None, y_pos=None, supply=0.0, price=0.0,
                 out_edges=None, in_edges=None):
        self.label = label
        self.x_pos, self.y_pos = x_pos, y_pos
        self.supply = supply

        self.price = price

        self.out_edges = out_edges if out_edges is not None else set()
        self.in_edges = in_edges if in_edges is not None else set()

    @property
    def surplus(self):
        """
        Return the surplus at the current node.
        """
        return self.supply + sum(edge.flow for edge in self.in_edges) \
            - sum(edge.flow for edge in self.out_edges)

    def push_lists(self, eps):
        """
        Returns a pair of collections containing the edges in this node's push
        list that are eps+ unblocked, followed by those that are eps- unblocked.
        """

        # TODO: Implement different epsilons for different edges.
        return set(e for e in self.out_edges if e.pos_unblocked(eps)), \
            set(e for e in self.in_edges if e.neg_unblocked(eps))

    @property
    def html(self):
        return """
            <strong>Node {}</strong>({}, {})<br />
            Supply: {}<br />
            Surplus: {}<br />
            Price: {}<br />
            """.format(self.label, self.x_pos, self.y_pos, self.supply,
                       self.surplus, self.price)

    def __repr__(self):
        return self.label if self.label is not None else "Node"


class Edge(object):
    def __init__(self, source, target, cost=0.0, capacity=None, min_flow=0.0,
                 flow=0.0):
        self.source = source
        self.target = target
        self.cost = cost
        self.capacity = capacity
        self.min_flow = min_flow
        self.flow = flow

    def pos_unblocked(self, eps):
        # TODO: Make this more robust to floating point error?
        return (self.capacity is None or self.flow < self.capacity) \
            and self.source.price == self.target.price + self.cost + eps

    def neg_unblocked(self, eps):
        return self.flow > self.min_flow \
            and self.target.price == self.source.price - self.cost + eps

    def html(self, eps):
        # TODO: Refactor so that eps is stored with each individual edge.
        output = "<strong>Edge {} &rarr; {}</strong>".format(
            self.source.label, self.target.label)

        pos_ub = self.pos_unblocked(eps)
        neg_ub = self.neg_unblocked(eps)
        if pos_ub and neg_ub:
            output += " (&epsilon;+/- unblocked)"
        elif pos_ub:
            output += " (&epsilon;+ unblocked)"
        elif neg_ub:
            output += " (&epsilon;- unblocked)"
        output += """<br />
            Cost: {}<br />
            Capacity: {}<br />
            Min: {}<br />
            Flow: {}<br />
            """.format(self.cost, self.capacity, self.min_flow, self.flow)

        return output

    def __repr__(self):
        return "Edge(" + self.source.__repr__() + " -> " + self.target.__repr__() + ")"
