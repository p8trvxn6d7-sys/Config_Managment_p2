def format_node(node):
    name, version = node
    return f"{name}@{version}" if version else name


def format_edges(node, children):
    targets = ", ".join(format_node(child) for child in children)
    return f"{format_node(node)} -> {targets or 'нет'}"


def print_cycles(cycles):
    if not cycles:
        print("Циклические зависимости: нет")
        return
    print("Циклические зависимости:")
    for cycle in cycles:
        print("  " + " -> ".join(format_node(node) for node in cycle))


def print_graph(root, graph, cycles):
    print(f"Граф зависимостей {format_node(root)}:")
    for node, children in graph.items():
        print(format_edges(node, children))
    print(f"Всего пакетов: {len(graph)}")
    print_cycles(cycles)
