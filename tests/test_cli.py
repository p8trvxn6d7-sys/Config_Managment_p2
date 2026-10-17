import contextlib
import io
import unittest

from depgraph.__main__ import EXIT_ERROR, EXIT_OK, main

URL = "https://registry.npmjs.org"


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
    def test_prints_key_value(self):
        args = ["--package", "express", "--repo", URL, "--version", "4.18.2"]
        code, out, _ = run(args)
        self.assertEqual(code, EXIT_OK)
        self.assertIn("package: express", out)
        self.assertIn(f"repo: {URL}", out)
        self.assertIn("test_mode: False", out)
        self.assertIn("version: 4.18.2", out)

    def test_test_mode(self):
        args = [
            "--package", "A",
            "--repo", "tests/data/repo.txt",
            "--test-mode",
            "--version", "1.0.0",
        ]
        code, out, _ = run(args)
        self.assertEqual(code, EXIT_OK)
        self.assertIn("test_mode: True", out)

    def test_validation_error(self):
        args = ["--package", "express", "--repo", URL, "--version", "x"]
        code, out, err = run(args)
        self.assertEqual(code, EXIT_ERROR)
        self.assertEqual(out, "")
        self.assertIn("Ошибка", err)

    def test_missing_option(self):
        code, _, err = run(["--package", "express"])
        self.assertNotEqual(code, EXIT_OK)
        self.assertIn("--repo", err)

    def test_unknown_option(self):
        args = ["--package", "a", "--repo", URL, "--version", "1.0.0", "--x"]
        code, _, _ = run(args)
        self.assertNotEqual(code, EXIT_OK)


if __name__ == "__main__":
    unittest.main()
