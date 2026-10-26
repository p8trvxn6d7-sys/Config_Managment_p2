import unittest

from depgraph.errors import RepoError
from depgraph.npm import build_url, extract_dependencies, fetch_dependencies
from fake_registry import make_server, server_url, stop_server

ROUTES = {
    "/debug/4.3.4": {"name": "debug", "dependencies": {"ms": "2.1.2"}},
    "/leaf/1.0.0": {"name": "leaf"},
    "/@babel%2Fcore/7.0.0": {"dependencies": {"a": "^1.0.0", "b": "~2.0.0"}},
    "/broken/1.0.0": b"not json",
    "/list/1.0.0": [1, 2],
    "/baddeps/1.0.0": {"dependencies": ["a"]},
}


class NpmTest(unittest.TestCase):
    def setUp(self):
        self.server = make_server(ROUTES)
        self.url = server_url(self.server)

    def tearDown(self):
        stop_server(self.server)

    def test_direct_dependencies(self):
        result = fetch_dependencies(self.url, "debug", "4.3.4")
        self.assertEqual(result, {"ms": "2.1.2"})

    def test_no_dependencies(self):
        self.assertEqual(fetch_dependencies(self.url, "leaf", "1.0.0"), {})

    def test_scoped_package(self):
        result = fetch_dependencies(self.url, "@babel/core", "7.0.0")
        self.assertEqual(result, {"a": "^1.0.0", "b": "~2.0.0"})

    def test_trailing_slash_in_repo(self):
        result = fetch_dependencies(self.url + "/", "debug", "4.3.4")
        self.assertEqual(result, {"ms": "2.1.2"})

    def test_package_not_found(self):
        with self.assertRaises(RepoError):
            fetch_dependencies(self.url, "missing", "1.0.0")

    def test_version_not_found(self):
        with self.assertRaises(RepoError):
            fetch_dependencies(self.url, "debug", "9.9.9")

    def test_invalid_json(self):
        with self.assertRaises(RepoError):
            fetch_dependencies(self.url, "broken", "1.0.0")

    def test_unexpected_format(self):
        for package in ("list", "baddeps"):
            with self.subTest(package=package):
                with self.assertRaises(RepoError):
                    fetch_dependencies(self.url, package, "1.0.0")

    def test_connection_refused(self):
        stop_server(self.server)
        with self.assertRaises(RepoError):
            fetch_dependencies(self.url, "debug", "4.3.4")
        self.server = make_server(ROUTES)

    def test_build_url(self):
        url = build_url("https://r.org/", "@babel/core", "7.0.0")
        self.assertEqual(url, "https://r.org/@babel%2Fcore/7.0.0")

    def test_extract_empty(self):
        self.assertEqual(extract_dependencies({}), {})


if __name__ == "__main__":
    unittest.main()
