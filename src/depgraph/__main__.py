import argparse
import sys
from dataclasses import asdict

from depgraph.config import ConfigError, build_config

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


def print_config(config):
    for key, value in asdict(config).items():
        print(f"{key}: {value}")


def main(argv=None):
    args = parse_args(argv)
    try:
        config = build_config(
            args.package, args.repo, args.test_mode, args.version
        )
    except ConfigError as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return EXIT_ERROR
    print_config(config)
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
