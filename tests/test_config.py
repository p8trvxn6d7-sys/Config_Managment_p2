import tempfile
import unittest

from depgraph.config import ConfigError, build_config

URL = "https://registry.npmjs.org"


class ConfigTest(unittest.TestCase):
    def repo_file(self):
        file = tempfile.NamedTemporaryFile("w", suffix=".txt")
        self.addCleanup(file.close)
        file.write("A: B\nB:\n")
        file.flush()
        return file.name

    def test_valid_url_mode(self):
        config = build_config("express", URL, False, "4.18.2")
        self.assertEqual(config.package, "express")
        self.assertFalse(config.test_mode)

    def test_valid_scoped_package(self):
        config = build_config("@babel/core", URL, False, "7.0.0")
        self.assertEqual(config.package, "@babel/core")

    def test_valid_prerelease_version(self):
        config = build_config("react", URL, False, "19.0.0-rc.1")
        self.assertEqual(config.version, "19.0.0-rc.1")

    def test_valid_test_mode(self):
        config = build_config("A", self.repo_file(), True, "1.0.0")
        self.assertTrue(config.test_mode)

    def test_empty_package(self):
        with self.assertRaises(ConfigError):
            build_config("", URL, False, "1.0.0")

    def test_bad_npm_package(self):
        with self.assertRaises(ConfigError):
            build_config("Bad Name", URL, False, "1.0.0")

    def test_too_long_package(self):
        with self.assertRaises(ConfigError):
            build_config("a" * 300, URL, False, "1.0.0")

    def test_lowercase_package_in_test_mode(self):
        with self.assertRaises(ConfigError):
            build_config("a", self.repo_file(), True, "1.0.0")

    def test_empty_repo(self):
        with self.assertRaises(ConfigError):
            build_config("express", "", False, "1.0.0")

    def test_bad_url_scheme(self):
        with self.assertRaises(ConfigError):
            build_config("express", "ftp://example.com", False, "1.0.0")

    def test_url_without_host(self):
        with self.assertRaises(ConfigError):
            build_config("express", "https://", False, "1.0.0")

    def test_url_with_spaces(self):
        with self.assertRaises(ConfigError):
            build_config("express", "https://a.com/a b", False, "1.0.0")

    def test_missing_file(self):
        with self.assertRaises(ConfigError):
            build_config("A", "no_such_file.txt", True, "1.0.0")

    def test_directory_instead_of_file(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ConfigError):
                build_config("A", folder, True, "1.0.0")

    def test_empty_version(self):
        with self.assertRaises(ConfigError):
            build_config("express", URL, False, "")

    def test_bad_version(self):
        for version in ("1.0", "v1.0.0", "latest", "1.0.0.0"):
            with self.subTest(version=version):
                with self.assertRaises(ConfigError):
                    build_config("express", URL, False, version)


if __name__ == "__main__":
    unittest.main()
