import contextlib
import io
import unittest

from depgraph.__main__ import EXIT_ERROR, EXIT_OK, main
from fake_registry import make_server, server_url, stop_server

ROUTES = {
    "/debug": {"versions": {"4.3.4": {"dependencies": {"ms": "2.1.2"}}}},
    "/ms": {"versions": {"2.1.2": {}}},
    "/app": {
        "versions": {"1.0.0": {"dependencies": {"lib": "^1.0.0"}}},
    },
    "/lib": {"versions": {"1.0.0": {}, "1.2.0": {}, "2.0.0": {}}},
    "/x": {"versions": {"1.0.0": {"dependencies": {"y": "^1.0.0"}}}},
    "/y": {"versions": {"1.0.0": {"dependencies": {"x": "^1.0.0"}}}},
}
DATA = "tests/data/"
LOAD_ORDER = "--load-order"


def run(args):
    out = io.StringIO()
    err = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = main(args)
        except SystemExit as exit_info:
            code = exit_info.code
    return code, out.getvalue(), err.getvalue()


class CliTest(unittest.TestCase):
    def start_registry(self):
        server = make_server(ROUTES)
        self.addCleanup(stop_server, server)
        return server_url(server)

    def run_npm(self, package, version, *extra):
        url = self.start_registry()
        return run(["--package", package, "--repo", url,
                    "--version", version, *extra])

    def run_file(self, package, name, *extra):
        return run(["--package", package, "--repo", DATA + name,
                    "--test-mode", "--version", "1.0.0", *extra])

    def test_prints_graph(self):
        code, out, _ = self.run_npm("debug", "4.3.4")
        self.assertEqual(code, EXIT_OK)
        self.assertIn("Граф зависимостей debug@4.3.4:", out)
        self.assertIn("debug@4.3.4 -> ms@2.1.2", out)
        self.assertIn("ms@2.1.2 -> нет", out)
        self.assertIn("Циклические зависимости: нет", out)

    def test_transitive_range_resolution(self):
        code, out, _ = self.run_npm("app", "1.0.0")
        self.assertEqual(code, EXIT_OK)
        self.assertIn("app@1.0.0 -> lib@1.2.0", out)

    def test_registry_cycle(self):
        code, out, _ = self.run_npm("x", "1.0.0")
        self.assertEqual(code, EXIT_OK)
        self.assertIn("Всего пакетов: 2", out)
        self.assertIn("  x@1.0.0 -> y@1.0.0 -> x@1.0.0", out)

    def test_package_not_found(self):
        code, out, err = self.run_npm("missing", "1.0.0")
        self.assertEqual(code, EXIT_ERROR)
        self.assertEqual(out, "")
        self.assertIn("Ошибка", err)

    def test_test_mode_diamond(self):
        code, out, _ = self.run_file("A", "repo.txt")
        self.assertEqual(code, EXIT_OK)
        for line in ("A -> B, C", "B -> D", "C -> D", "D -> нет"):
            self.assertIn(line, out)
        self.assertIn("Всего пакетов: 4", out)

    def test_test_mode_cycle(self):
        code, out, _ = self.run_file("A", "cycle.txt")
        self.assertEqual(code, EXIT_OK)
        self.assertIn("  A -> B -> C -> A", out)

    def test_test_mode_self_dependency(self):
        code, out, _ = self.run_file("A", "selfloop.txt")
        self.assertEqual(code, EXIT_OK)
        self.assertIn("  A -> A", out)

    def test_test_mode_unknown_package(self):
        code, _, err = self.run_file("Z", "repo.txt")
        self.assertEqual(code, EXIT_ERROR)
        self.assertIn("Ошибка", err)

    def test_graph_is_default_output(self):
        code, out, _ = self.run_file("A", "repo.txt")
        self.assertEqual(code, EXIT_OK)
        self.assertIn("Граф зависимостей", out)
        self.assertNotIn("Порядок загрузки", out)

    def test_load_order_diamond(self):
        code, out, _ = self.run_file("A", "repo.txt", LOAD_ORDER)
        self.assertEqual(code, EXIT_OK)
        self.assertIn("Порядок загрузки зависимостей A:", out)
        self.assertIn("1. D\n2. B\n3. C\n4. A\n", out)
        self.assertIn("Разорванные циклические связи: нет", out)
        self.assertNotIn("Граф зависимостей", out)

    def test_load_order_larger_graph(self):
        code, out, _ = self.run_file("A", "order.txt", LOAD_ORDER)
        self.assertEqual(code, EXIT_OK)
        expected = "1. D\n2. G\n3. E\n4. B\n5. F\n6. C\n7. A\n"
        self.assertIn(expected, out)

    def test_load_order_of_inner_package(self):
        code, out, _ = self.run_file("B", "order.txt", LOAD_ORDER)
        self.assertEqual(code, EXIT_OK)
        self.assertIn("1. D\n2. G\n3. E\n4. B\n", out)
        self.assertNotIn(". A\n", out)

    def test_load_order_cycle(self):
        code, out, _ = self.run_file("A", "cycle.txt", LOAD_ORDER)
        self.assertEqual(code, EXIT_OK)
        self.assertIn("1. D\n2. C\n3. B\n4. A\n", out)
        self.assertIn("Разорванные циклические связи:\n  C -> A", out)

    def test_load_order_self_dependency(self):
        code, out, _ = self.run_file("A", "selfloop.txt", LOAD_ORDER)
        self.assertEqual(code, EXIT_OK)
        self.assertIn("1. B\n2. A\n", out)
        self.assertIn("  A -> A", out)

    def test_load_order_npm(self):
        code, out, _ = self.run_npm("app", "1.0.0", LOAD_ORDER)
        self.assertEqual(code, EXIT_OK)
        self.assertIn("1. lib@1.2.0\n2. app@1.0.0\n", out)

    def test_load_order_registry_cycle(self):
        code, out, _ = self.run_npm("x", "1.0.0", LOAD_ORDER)
        self.assertEqual(code, EXIT_OK)
        self.assertIn("1. y@1.0.0\n2. x@1.0.0\n", out)
        self.assertIn("  y@1.0.0 -> x@1.0.0", out)

    def test_load_order_unknown_package(self):
        code, out, err = self.run_file("Z", "repo.txt", LOAD_ORDER)
        self.assertEqual(code, EXIT_ERROR)
        self.assertEqual(out, "")
        self.assertIn("Ошибка", err)

    def test_validation_error(self):
        code, out, err = self.run_npm("debug", "x")
        self.assertEqual(code, EXIT_ERROR)
        self.assertEqual(out, "")
        self.assertIn("Ошибка", err)

    def test_missing_option(self):
        code, _, err = run(["--package", "express"])
        self.assertNotEqual(code, EXIT_OK)
        self.assertIn("--repo", err)

    def test_unknown_option(self):
        url = self.start_registry()
        args = ["--package", "debug", "--repo", url, "--version",
                "4.3.4", "--x"]
        code, _, _ = run(args)
        self.assertNotEqual(code, EXIT_OK)


if __name__ == "__main__":
    unittest.main()
