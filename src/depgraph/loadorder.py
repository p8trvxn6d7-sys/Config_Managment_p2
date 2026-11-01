IN_PROGRESS = 1
DONE = 2


def visit_child(node, child, state, stack, graph):
    if state.get(child) == IN_PROGRESS:
        return (node, child)
    if child not in state:
        state[child] = IN_PROGRESS
        stack.append((child, iter(graph[child])))
    return None


def load_order(graph, root):
    order = []
    skipped = []
    state = {root: IN_PROGRESS}
    stack = [(root, iter(graph[root]))]
    while stack:
        node, children = stack[-1]
        child = next(children, None)
        if child is None:
            state[node] = DONE
            order.append(node)
            stack.pop()
            continue
        edge = visit_child(node, child, state, stack, graph)
        if edge:
            skipped.append(edge)
    return order, skipped
