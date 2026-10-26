import argparse
import sys

from depgraph.config import build_config
from depgraph.errors import ConfigError, RepoError
from depgraph.npm import fetch_dependencies
from depgraph.testrepo import load_dependencies

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
    return parser.parse_args(argv)


def collect_dependencies(config):
    if config.test_mode:
        return load_dependencies(config.repo, config.package)
    return fetch_dependencies(config.repo, config.package, config.version)


def format_dependency(name, spec):
    return f"{name}: {spec}" if spec else name


def print_dependencies(config, dependencies):
    print(f"Прямые зависимости {config.package}@{config.version}:")
    if not dependencies:
        print("нет")
    for name, spec in dependencies.items():
        print(format_dependency(name, spec))


def main(argv=None):
    args = parse_args(argv)
    try:
        config = build_config(
            args.package, args.repo, args.test_mode, args.version
        )
        dependencies = collect_dependencies(config)
    except (ConfigError, RepoError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return EXIT_ERROR
    print_dependencies(config, dependencies)
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
