import unittest

from depgraph.errors import RepoError
from depgraph.npm import NpmSource
from depgraph.testrepo import FileSource
from fake_registry import make_server, server_url, stop_server

ROUTES = {
    "/app": {
        "dist-tags": {"latest": "2.0.0", "next": "3.0.0-rc.1"},
        "versions": {
            "1.0.0": {"dependencies": {"lib": "^1.0.0"}},
            "2.0.0": {"dependencies": {"lib": "^1.0.0", "tool": "latest"}},
        },
    },
    "/lib": {
        "dist-tags": {"latest": "2.0.0"},
        "versions": {"1.0.0": {}, "1.2.0": {}, "2.0.0": {}},
    },
    "/@scope%2Fpkg": {"versions": {"1.0.0": {}}},
    "/list": [1, 2],
    "/badversions": {"versions": []},
}
GRAPH_FILE = "tests/data/repo.txt"


class NpmSourceTest(unittest.TestCase):
    def source(self):
        server = make_server(ROUTES)
        self.addCleanup(stop_server, server)
        return NpmSource(server_url(server))

    def test_resolve_range(self):
        self.assertEqual(self.source().resolve("lib", "^1.0.0"), "1.2.0")

    def test_resolve_dist_tag(self):
        self.assertEqual(self.source().resolve("lib", "latest"), "2.0.0")
        self.assertEqual(self.source().resolve("app", "next"), "3.0.0-rc.1")

    def test_resolve_scoped(self):
        self.assertEqual(self.source().resolve("@scope/pkg", "*"), "1.0.0")

    def test_no_matching_version(self):
        with self.assertRaises(RepoError):
            self.source().resolve("lib", "^5.0.0")

    def test_unknown_package(self):
        with self.assertRaises(RepoError):
            self.source().resolve("missing", "*")

    def test_dependencies(self):
        result = self.source().dependencies("app", "2.0.0")
        self.assertEqual(result, {"lib": "^1.0.0", "tool": "latest"})

    def test_no_dependencies(self):
        self.assertEqual(self.source().dependencies("lib", "1.0.0"), {})

    def test_unknown_version(self):
        with self.assertRaises(RepoError):
            self.source().dependencies("app", "9.9.9")

    def test_unexpected_document(self):
        for package in ("list", "badversions"):
            with self.subTest(package=package):
                with self.assertRaises(RepoError):
                    self.source().resolve(package, "*")

    def test_document_is_cached(self):
        source = self.source()
        self.assertIs(source.document("lib"), source.document("lib"))


class FileSourceTest(unittest.TestCase):
    def test_dependencies(self):
        source = FileSource(GRAPH_FILE)
        self.assertEqual(source.dependencies("A", ""), {"B": "", "C": ""})

    def test_resolve_returns_empty_version(self):
        self.assertEqual(FileSource(GRAPH_FILE).resolve("B", ""), "")

    def test_unknown_package(self):
        with self.assertRaises(RepoError):
            FileSource(GRAPH_FILE).dependencies("Z", "")


if __name__ == "__main__":
    unittest.main()
