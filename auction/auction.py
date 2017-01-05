"""Implementations of various auction algorithms for min-cost flows."""

# TODO: If needed, make this quick-and-dirty implementation less inefficient.

def min_cost_flow(eps, graph, get_iter_nodes=None, select_edge=None,
                  get_delta=None, visualizer=None, max_iter=None,
                  debug=False):
    """A general template for implementations of the generic algorithm for
    min-cost network flows. This function is left as general as possible, so
    that its behaviour may be specified at runtime by passing as input functions
    that implement parts of the generic algorithm that are left unspecified.
    """

    if select_edge is None:
        select_edge = any_edge

    if visualizer is None:
        visualize = lambda *args: None  # Do-nothing visualization.
    else:
        visualize = lambda graph: visualizer.draw_graph(graph)

    # TODO: Detect infeasibility. For now, assume the problem is feasible.

    # TODO: Make checking for stopping condition more efficient.
    pos_surplus = set(node for node in graph.nodes if node.surplus > 0)
    iteration = 0
    if debug:
        visualize(graph)
        input("Iteration {}: Press ENTER to continue.".format(iteration))
    while (max_iter is None or iteration < max_iter) and pos_surplus:
        # Perform delta-pushes.
        # Get all nodes where we attempt to perform delta-pushes.
        iter_nodes = get_iter_nodes(pos_surplus)

        for node in iter_nodes:
            pos, neg = node.push_lists(eps)
            edge = select_edge(pos, neg)
            while edge is not None and node.surplus > 0:
                # Perform a delta-push.
                delta = get_delta(node, edge)
                if debug:
                    visualize(graph)
                    input("Performing {} push at node {} on {}. ".format(delta, node.label, edge))
                edge.flow += delta

                pos, neg = node.push_lists(eps)
                edge = select_edge(pos, neg)

        # Perform price rises. TODO: Should we use the same iter_nodes?
        # Here, we use I = iter_nodes. TODO: Support this operation without
        # iterating over the entire graph.
        out_vals = [edge.target.price + edge.cost + eps - edge.source.price
            for edge in graph.edges
                if edge.source in iter_nodes
                    and edge.target not in iter_nodes
                    and (edge.capacity is None or edge.flow < edge.capacity)]
        in_vals = [edge.source.price - edge.cost + eps - edge.target.price
            for edge in graph.edges
                if edge.source not in iter_nodes
                    and edge.target in iter_nodes
                    and edge.flow > edge.min_flow]
        price_rise_vals = out_vals + in_vals

        gamma = 0
        if price_rise_vals:
            gamma = min(price_rise_vals)

        for node in iter_nodes:
            node.price += gamma

        # Recompute nodes with positive surplus. TODO: Make this less naive.
        pos_surplus = set(node for node in graph.nodes if node.surplus > 0)
        iteration += 1

        if debug:
            visualize(graph)
            input("Iteration {}: Press ENTER to continue.".format(iteration))

    return True

def any_node(pos_surplus):
    # TODO: This really shouldn't remove the element.
    return set([pos_surplus.pop()])

def any_edge(pos, neg):
    if pos:
        return set(pos).pop()
    if neg:
        return set(neg).pop()
    return None

def er_delta(node, edge):
    if edge.source == node:
        return min(node.surplus, edge.cost - edge.flow)
    elif edge.target == node:
        return -min(node.surplus, edge.flow - edge.min_flow)
    raise

def er_min_cost_flow(eps, graph, visualizer=None, max_iter=None,
                     debug=False):
    return min_cost_flow(eps, graph, any_node, any_edge, er_delta,
                         visualizer, max_iter, debug)
