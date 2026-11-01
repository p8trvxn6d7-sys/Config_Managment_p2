from collections import deque


def child_nodes(source, node):
    name, version = node
    dependencies = source.dependencies(name, version)
    return [
        (dependency, source.resolve(dependency, spec))
        for dependency, spec in dependencies.items()
    ]


def expand_level(source, level, graph):
    next_level = []
    for node in level:
        if node in graph:
            continue
        children = child_nodes(source, node)
        graph[node] = children
        next_level.extend(children)
    if next_level:
        expand_level(source, next_level, graph)


def build_graph(source, root):
    graph = {}
    expand_level(source, [root], graph)
    return graph


def trace_path(parents, node, start):
    path = [node]
    while path[-1] != start:
        path.append(parents[path[-1]])
    path.reverse()
    return path + [start]


def cycle_through(graph, start):
    parents = {}
    queue = deque([start])
    while queue:
        node = queue.popleft()
        for child in graph.get(node, []):
            if child == start:
                return trace_path(parents, node, start)
            if child not in parents:
                parents[child] = node
                queue.append(child)
    return None


def find_cycles(graph):
    cycles = []
    seen = set()
    for node in graph:
        cycle = cycle_through(graph, node)
        if cycle is None or frozenset(cycle) in seen:
            continue
        seen.add(frozenset(cycle))
        cycles.append(cycle)
    return cycles
