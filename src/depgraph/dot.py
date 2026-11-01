from depgraph.report import format_node

INDENT = "    "
ROOT_STYLE = "style=filled, fillcolor=lightblue"


def quote(text):
    escaped = text.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def node_statement(node, root):
    attributes = f" [{ROOT_STYLE}]" if node == root else ""
    return f"{INDENT}{quote(format_node(node))}{attributes};"


def edge_statements(node, children):
    source = quote(format_node(node))
    return [
        f"{INDENT}{source} -> {quote(format_node(child))};"
        for child in children
    ]


def build_dot(root, graph):
    lines = [f"digraph {quote(format_node(root))} {{"]
    lines.append(f"{INDENT}node [shape=box];")
    lines.extend(node_statement(node, root) for node in graph)
    for node, children in graph.items():
        lines.extend(edge_statements(node, children))
    lines.append("}")
    return "\n".join(lines)
