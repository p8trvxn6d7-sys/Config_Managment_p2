import argparse
import sys

from depgraph.config import build_config
from depgraph.dot import build_dot
from depgraph.errors import ConfigError, RepoError
from depgraph.graph import build_graph, find_cycles
from depgraph.loadorder import load_order
from depgraph.npm import NpmSource
from depgraph.report import print_graph, print_load_order
from depgraph.testrepo import FileSource

EXIT_OK = 0
EXIT_ERROR = 1


def parse_args(argv):
    parser = argparse.ArgumentParser(
        prog="depgraph",
        description="Визуализация графа зависимостей npm-пакета",
        allow_abbrev=False,
    )
    parser.add_argument("--package", required=True, help="имя пакета")
    parser.add_argument(
        "--repo",
        required=True,
        help="URL репозитория или путь к файлу тестового репозитория",
    )
    parser.add_argument(
        "--test-mode",
        action="store_true",
        help="режим работы с тестовым репозиторием",
    )
    parser.add_argument("--version", required=True, help="версия пакета")
    output = parser.add_mutually_exclusive_group()
    output.add_argument(
        "--load-order",
        action="store_true",
        help="вывести порядок загрузки зависимостей пакета",
    )
    output.add_argument(
        "--graphviz",
        action="store_true",
        help="вывести граф зависимостей на языке Graphviz (DOT)",
    )
    return parser.parse_args(argv)


def make_source(config):
    if config.test_mode:
        return FileSource(config.repo)
    return NpmSource(config.repo)


def root_node(config):
    version = "" if config.test_mode else config.version
    return (config.package, version)


def analyze(config):
    root = root_node(config)
    graph = build_graph(make_source(config), root)
    return root, graph, find_cycles(graph)


def show_result(args, root, graph, cycles):
    if args.load_order:
        order, skipped = load_order(graph, root)
        print_load_order(root, order, skipped)
    elif args.graphviz:
        print(build_dot(root, graph))
    else:
        print_graph(root, graph, cycles)


def report_error(message):
    print(f"Ошибка: {message}", file=sys.stderr)
    return EXIT_ERROR


def main(argv=None):
    args = parse_args(argv)
    try:
        config = build_config(
            args.package, args.repo, args.test_mode, args.version
        )
        root, graph, cycles = analyze(config)
    except (ConfigError, RepoError) as error:
        return report_error(error)
    except RecursionError:
        return report_error("граф зависимостей слишком глубокий")
    show_result(args, root, graph, cycles)
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
