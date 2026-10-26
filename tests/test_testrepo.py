import os
import tempfile
import unittest

from depgraph.errors import RepoError
from depgraph.testrepo import load_dependencies


class TestRepoTest(unittest.TestCase):
    def write(self, text):
        file = tempfile.NamedTemporaryFile(
            "w", suffix=".txt", delete=False, encoding="utf-8"
        )
        file.write(text)
        file.close()
        self.addCleanup(os.remove, file.name)
        return file.name

    def test_direct_dependencies(self):
        path = self.write("A: B C\nB: D\nC:\nD:\n")
        self.assertEqual(load_dependencies(path, "A"), {"B": "", "C": ""})

    def test_no_dependencies(self):
        path = self.write("A: B\nB:\n")
        self.assertEqual(load_dependencies(path, "B"), {})

    def test_blank_lines_ignored(self):
        path = self.write("\nA: B\n\nB:\n")
        self.assertEqual(load_dependencies(path, "A"), {"B": ""})

    def test_package_not_in_file(self):
        path = self.write("A: B\nB:\n")
        with self.assertRaises(RepoError):
            load_dependencies(path, "Z")

    def test_line_without_colon(self):
        path = self.write("A B\n")
        with self.assertRaises(RepoError):
            load_dependencies(path, "A")

    def test_lowercase_dependency(self):
        path = self.write("A: b\n")
        with self.assertRaises(RepoError):
            load_dependencies(path, "A")

    def test_lowercase_package_name(self):
        path = self.write("a: B\n")
        with self.assertRaises(RepoError):
            load_dependencies(path, "A")


if __name__ == "__main__":
    unittest.main()
