import unittest

from depgraph.loadorder import load_order

DEPTH = 5000
ORDER_TEXT = "A: B C\nB: D E\nC: E F\nD:\nE: G\nF: G\nG:"
ROOT = ("A", "")


def node(name):
    return (name, "")


def make_graph(text):
    graph = {}
    for line in text.splitlines():
        name, _, rest = line.partition(":")
        graph[node(name.strip())] = [node(item) for item in rest.split()]
    return graph


def names(nodes):
    return [name for name, _ in nodes]


class LoadOrderTest(unittest.TestCase):
    def order_of(self, text):
        order, skipped = load_order(make_graph(text), ROOT)
        return names(order), skipped

    def test_single_package(self):
        self.assertEqual(self.order_of("A:"), (["A"], []))

    def test_chain(self):
        order, _ = self.order_of("A: B\nB: C\nC:")
        self.assertEqual(order, ["C", "B", "A"])

    def test_dependency_before_dependent(self):
        order, _ = self.order_of("A: B C\nB: D\nC: D\nD:")
        self.assertEqual(order, ["D", "B", "C", "A"])

    def test_larger_graph_exact_order(self):
        order, skipped = self.order_of(ORDER_TEXT)
        self.assertEqual(order, ["D", "G", "E", "B", "F", "C", "A"])
        self.assertEqual(skipped, [])

    def test_each_package_once(self):
        order, _ = self.order_of(ORDER_TEXT)
        self.assertEqual(len(order), len(set(order)))

    def test_every_dependency_precedes_dependent(self):
        graph = make_graph(ORDER_TEXT)
        order, _ = load_order(graph, ROOT)
        position = {item: index for index, item in enumerate(order)}
        for item, children in graph.items():
            for child in children:
                self.assertLess(position[child], position[item])

    def test_root_is_last(self):
        order, _ = self.order_of(ORDER_TEXT)
        self.assertEqual(order[-1], "A")

    def test_cycle_is_broken(self):
        order, skipped = self.order_of("A: B\nB: C\nC: A D\nD:")
        self.assertEqual(order, ["D", "C", "B", "A"])
        self.assertEqual(skipped, [(node("C"), node("A"))])

    def test_self_dependency(self):
        order, skipped = self.order_of("A: A B\nB:")
        self.assertEqual(order, ["B", "A"])
        self.assertEqual(skipped, [(node("A"), node("A"))])

    def test_unreachable_packages_are_ignored(self):
        order, _ = self.order_of("A: B\nB:\nX: Y\nY:")
        self.assertEqual(order, ["B", "A"])

    def test_deep_chain_without_recursion(self):
        graph = {(str(i), ""): [(str(i + 1), "")] for i in range(DEPTH)}
        graph[(str(DEPTH), "")] = []
        order, skipped = load_order(graph, ("0", ""))
        self.assertEqual(len(order), DEPTH + 1)
        self.assertEqual(order[0], (str(DEPTH), ""))
        self.assertEqual(skipped, [])


if __name__ == "__main__":
    unittest.main()
