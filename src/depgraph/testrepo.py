import re

from depgraph.errors import RepoError

NAME = re.compile(r"^[A-Z]+$")


def parse_line(line, number):
    name, separator, rest = line.partition(":")
    name = name.strip()
    if not separator or not NAME.match(name):
        raise RepoError(f"строка {number}: ожидается формат 'A: B C'")
    dependencies = rest.split()
    for dependency in dependencies:
        if not NAME.match(dependency):
            raise RepoError(
                f"строка {number}: недопустимое имя пакета {dependency}"
            )
    return name, dependencies


def load_graph(path):
    graph = {}
    with open(path, encoding="utf-8") as stream:
        for number, line in enumerate(stream, start=1):
            if line.strip():
                name, dependencies = parse_line(line, number)
                graph[name] = dependencies
    return graph


def load_dependencies(path, package):
    graph = load_graph(path)
    if package not in graph:
        raise RepoError(f"пакет {package} не найден в {path}")
    return {name: "" for name in graph[package]}
