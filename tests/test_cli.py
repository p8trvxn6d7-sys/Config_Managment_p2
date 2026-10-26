import contextlib
import io
import unittest

from depgraph.__main__ import EXIT_ERROR, EXIT_OK, main
from fake_registry import make_server, server_url, stop_server

ROUTES = {
    "/debug/4.3.4": {"dependencies": {"ms": "2.1.2"}},
    "/leaf/1.0.0": {},
}
TEST_REPO = "tests/data/repo.txt"


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
    def setUp(self):
        self.server = make_server(ROUTES)
        self.url = server_url(self.server)

    def tearDown(self):
        stop_server(self.server)

    def args(self, package, version):
        return ["--package", package, "--repo", self.url,
                "--version", version]

    def test_prints_dependencies(self):
        code, out, _ = run(self.args("debug", "4.3.4"))
        self.assertEqual(code, EXIT_OK)
        self.assertIn("Прямые зависимости debug@4.3.4:", out)
        self.assertIn("ms: 2.1.2", out)

    def test_no_dependencies(self):
        code, out, _ = run(self.args("leaf", "1.0.0"))
        self.assertEqual(code, EXIT_OK)
        self.assertIn("нет", out)

    def test_package_not_found(self):
        code, out, err = run(self.args("missing", "1.0.0"))
        self.assertEqual(code, EXIT_ERROR)
        self.assertEqual(out, "")
        self.assertIn("Ошибка", err)

    def test_test_mode(self):
        args = ["--package", "A", "--repo", TEST_REPO, "--test-mode",
                "--version", "1.0.0"]
        code, out, _ = run(args)
        self.assertEqual(code, EXIT_OK)
        self.assertIn("B", out)
        self.assertIn("C", out)

    def test_test_mode_unknown_package(self):
        args = ["--package", "Z", "--repo", TEST_REPO, "--test-mode",
                "--version", "1.0.0"]
        code, _, err = run(args)
        self.assertEqual(code, EXIT_ERROR)
        self.assertIn("Ошибка", err)

    def test_validation_error(self):
        code, out, err = run(self.args("debug", "x"))
        self.assertEqual(code, EXIT_ERROR)
        self.assertEqual(out, "")
        self.assertIn("Ошибка", err)

    def test_missing_option(self):
        code, _, err = run(["--package", "express"])
        self.assertNotEqual(code, EXIT_OK)
        self.assertIn("--repo", err)

    def test_unknown_option(self):
        code, _, _ = run(self.args("debug", "4.3.4") + ["--x"])
        self.assertNotEqual(code, EXIT_OK)


if __name__ == "__main__":
    unittest.main()
