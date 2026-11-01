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


def print_skipped_edges(skipped):
    if not skipped:
        print("Разорванные циклические связи: нет")
        return
    print("Разорванные циклические связи:")
    for source, target in skipped:
        print(f"  {format_node(source)} -> {format_node(target)}")


def print_load_order(root, order, skipped):
    print(f"Порядок загрузки зависимостей {format_node(root)}:")
    for index, node in enumerate(order, start=1):
        print(f"{index}. {format_node(node)}")
    print_skipped_edges(skipped)


def print_graph(root, graph, cycles):
    print(f"Граф зависимостей {format_node(root)}:")
    for node, children in graph.items():
        print(format_edges(node, children))
    print(f"Всего пакетов: {len(graph)}")
    print_cycles(cycles)
