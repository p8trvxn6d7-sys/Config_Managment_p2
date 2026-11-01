import unittest

from depgraph.dot import build_dot, quote

ROOT = ("A", "")


def node(name, version=""):
    return (name, version)


class QuoteTest(unittest.TestCase):
    def test_plain(self):
        self.assertEqual(quote("A"), '"A"')

    def test_scoped_package(self):
        self.assertEqual(quote("@babel/core@7.0.0"), '"@babel/core@7.0.0"')

    def test_double_quote_is_escaped(self):
        self.assertEqual(quote('a"b'), '"a\\"b"')

    def test_backslash_is_escaped(self):
        self.assertEqual(quote("a\\b"), '"a\\\\b"')


class BuildDotTest(unittest.TestCase):
    def test_single_package(self):
        text = build_dot(ROOT, {ROOT: []})
        expected = "\n".join([
            'digraph "A" {',
            "    node [shape=box];",
            '    "A" [style=filled, fillcolor=lightblue];',
            "}",
        ])
        self.assertEqual(text, expected)

    def test_edges(self):
        graph = {ROOT: [node("B"), node("C")], node("B"): [], node("C"): []}
        lines = build_dot(ROOT, graph).splitlines()
        self.assertIn('    "A" -> "B";', lines)
        self.assertIn('    "A" -> "C";', lines)

    def test_isolated_node_is_declared(self):
        graph = {ROOT: [node("B")], node("B"): []}
        self.assertIn('    "B";', build_dot(ROOT, graph).splitlines())

    def test_each_node_declared_once(self):
        graph = {
            ROOT: [node("B"), node("C")],
            node("B"): [node("D")],
            node("C"): [node("D")],
            node("D"): [],
        }
        lines = build_dot(ROOT, graph).splitlines()
        self.assertEqual(lines.count('    "D";'), 1)

    def test_only_root_is_highlighted(self):
        graph = {ROOT: [node("B")], node("B"): []}
        text = build_dot(ROOT, graph)
        self.assertEqual(text.count("fillcolor"), 1)

    def test_versions_in_names(self):
        root = node("app", "1.0.0")
        graph = {root: [node("lib", "1.2.0")], node("lib", "1.2.0"): []}
        text = build_dot(root, graph)
        self.assertTrue(text.startswith('digraph "app@1.0.0" {'))
        self.assertIn('    "app@1.0.0" -> "lib@1.2.0";', text)

    def test_cycle_edges_are_kept(self):
        graph = {ROOT: [node("B")], node("B"): [ROOT]}
        lines = build_dot(ROOT, graph).splitlines()
        self.assertIn('    "B" -> "A";', lines)

    def test_self_dependency(self):
        lines = build_dot(ROOT, {ROOT: [ROOT]}).splitlines()
        self.assertIn('    "A" -> "A";', lines)

    def test_document_is_closed(self):
        text = build_dot(ROOT, {ROOT: []})
        self.assertTrue(text.endswith("\n}"))
        self.assertEqual(text.count("{"), text.count("}"))


if __name__ == "__main__":
    unittest.main()
