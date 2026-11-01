import unittest

from depgraph.graph import build_graph, find_cycles


class DictSource:
    def __init__(self, graph):
        self.graph = graph
        self.requested = []

    def resolve(self, package, spec):
        return ""

    def dependencies(self, package, version):
        self.requested.append(package)
        return {name: "" for name in self.graph[package]}


def node(name):
    return (name, "")


def names(graph):
    return [name for name, _ in graph]


class GraphTest(unittest.TestCase):
    def build(self, text):
        graph = {}
        for line in text.splitlines():
            name, _, rest = line.partition(":")
            graph[name.strip()] = rest.split()
        source = DictSource(graph)
        return source, build_graph(source, node("A"))

    def test_single_package(self):
        _, graph = self.build("A:")
        self.assertEqual(graph, {node("A"): []})

    def test_edges(self):
        _, graph = self.build("A: B C\nB:\nC:")
        self.assertEqual(graph[node("A")], [node("B"), node("C")])

    def test_diamond_visits_each_package_once(self):
        source, graph = self.build("A: B C\nB: D\nC: D\nD:")
        self.assertEqual(names(graph), ["A", "B", "C", "D"])
        self.assertEqual(sorted(source.requested), ["A", "B", "C", "D"])

    def test_breadth_first_order(self):
        _, graph = self.build("A: B C\nB: E\nC: F\nE:\nF:")
        self.assertEqual(names(graph), ["A", "B", "C", "E", "F"])

    def test_cycle_terminates(self):
        _, graph = self.build("A: B\nB: C\nC: A D\nD:")
        self.assertEqual(names(graph), ["A", "B", "C", "D"])
        self.assertIn(node("A"), graph[node("C")])

    def test_self_dependency(self):
        _, graph = self.build("A: A B\nB:")
        self.assertEqual(names(graph), ["A", "B"])

    def test_find_cycle(self):
        _, graph = self.build("A: B\nB: C\nC: A D\nD:")
        expected = [[node("A"), node("B"), node("C"), node("A")]]
        self.assertEqual(find_cycles(graph), expected)

    def test_find_self_cycle(self):
        _, graph = self.build("A: A\n")
        self.assertEqual(find_cycles(graph), [[node("A"), node("A")]])

    def test_no_cycles(self):
        _, graph = self.build("A: B C\nB: D\nC: D\nD:")
        self.assertEqual(find_cycles(graph), [])

    def test_two_separate_cycles(self):
        text = "A: B C\nB: A\nC: D\nD: C"
        _, graph = self.build(text)
        self.assertEqual(len(find_cycles(graph)), 2)


if __name__ == "__main__":
    unittest.main()
