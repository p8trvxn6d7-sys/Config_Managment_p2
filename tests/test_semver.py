import unittest

from depgraph.errors import RepoError
from depgraph.semver import max_satisfying, parse_version


class SemverTest(unittest.TestCase):
    def check(self, versions, spec, expected):
        self.assertEqual(max_satisfying(versions, spec), expected)

    def test_caret(self):
        versions = ["1.0.0", "1.2.0", "1.9.9", "2.0.0"]
        self.check(versions, "^1.0.0", "1.9.9")

    def test_caret_zero_minor(self):
        self.check(["0.2.3", "0.2.9", "0.3.0"], "^0.2.3", "0.2.9")

    def test_caret_zero_patch(self):
        self.check(["0.0.3", "0.0.4"], "^0.0.3", "0.0.3")

    def test_tilde(self):
        self.check(["1.2.3", "1.2.9", "1.3.0"], "~1.2.3", "1.2.9")

    def test_tilde_partial(self):
        self.check(["1.2.0", "1.2.5", "1.3.0"], "~1.2", "1.2.5")

    def test_x_range(self):
        versions = ["0.9.0", "1.0.0", "1.5.0", "2.0.0"]
        self.check(versions, "1.x", "1.5.0")

    def test_any(self):
        self.check(["1.0.0", "2.0.0-beta.1"], "*", "1.0.0")
        self.check(["1.0.0", "3.1.0"], "", "3.1.0")

    def test_exact(self):
        self.check(["1.2.3", "1.2.4"], "1.2.3", "1.2.3")

    def test_comparators(self):
        versions = ["1.1.0", "1.2.0", "1.4.9", "1.5.0"]
        self.check(versions, ">=1.2.0 <1.5.0", "1.4.9")
        self.check(versions, ">= 1.2.0 < 1.5.0", "1.4.9")

    def test_greater_and_less(self):
        self.check(["1.2.3", "1.2.4"], ">1.2.3", "1.2.4")
        self.check(["1.2.2", "1.2.3"], "<1.2.3", "1.2.2")
        self.check(["1.2.9", "1.3.0"], "<=1.2", "1.2.9")
        self.check(["1.2.9", "1.3.0"], ">1.2", "1.3.0")

    def test_or(self):
        versions = ["1.0.0", "1.5.0", "2.3.0", "3.0.0"]
        self.check(versions, "1.0.0 || 2.x", "2.3.0")

    def test_hyphen(self):
        versions = ["1.2.2", "1.2.3", "2.3.4", "2.3.5"]
        self.check(versions, "1.2.3 - 2.3.4", "2.3.4")
        self.check(["2.3.9", "2.4.0"], "1.2 - 2.3", "2.3.9")

    def test_prerelease_only(self):
        versions = ["2.0.0-beta.1", "2.0.0-beta.2"]
        self.check(versions, "^2.0.0-beta.1", "2.0.0-beta.2")

    def test_prerelease_excluded_from_upper_bound(self):
        self.check(["1.5.0", "2.0.0-alpha"], "^1.0.0", "1.5.0")

    def test_no_match(self):
        self.check(["1.0.0"], "^2.0.0", None)

    def test_unsupported_spec(self):
        for spec in ("git+https://x.org/r.git", "file:../lib", ">="):
            with self.subTest(spec=spec):
                with self.assertRaises(RepoError):
                    max_satisfying(["1.0.0"], spec)

    def test_invalid_versions_skipped(self):
        self.check(["bad", "1.0.0"], "*", "1.0.0")

    def test_version_order(self):
        order = [
            "1.0.0-alpha",
            "1.0.0-alpha.1",
            "1.0.0-alpha.beta",
            "1.0.0-beta.2",
            "1.0.0-beta.11",
            "1.0.0",
        ]
        keys = [parse_version(item) for item in order]
        self.assertEqual(keys, sorted(keys))

    def test_parse_version(self):
        self.assertEqual(parse_version("v1.2.3+b"), parse_version("1.2.3"))
        self.assertIsNone(parse_version("1.2"))


if __name__ == "__main__":
    unittest.main()
