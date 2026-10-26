import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from depgraph.errors import ConfigError

NPM_NAME = re.compile(
    r"^(@[a-z0-9-~][a-z0-9-._~]*/)?[a-z0-9-~][a-z0-9-._~]*$"
)
TEST_NAME = re.compile(r"^[A-Z]+$")
VERSION = re.compile(
    r"^\d+\.\d+\.\d+(-[0-9A-Za-z.-]+)?(\+[0-9A-Za-z.-]+)?$"
)
URL_SCHEMES = ("http", "https")
MAX_NAME_LENGTH = 214


@dataclass(frozen=True)
class Config:
    package: str
    repo: str
    test_mode: bool
    version: str


def validate_package(name, test_mode):
    if not name:
        raise ConfigError("имя пакета не задано")
    if len(name) > MAX_NAME_LENGTH:
        raise ConfigError("имя пакета слишком длинное")
    if test_mode:
        if not TEST_NAME.match(name):
            raise ConfigError(
                "в тестовом режиме имя пакета - большие латинские буквы"
            )
    elif not NPM_NAME.match(name):
        raise ConfigError(f"недопустимое имя npm-пакета: {name}")


def validate_url(url):
    parsed = urlparse(url)
    if parsed.scheme not in URL_SCHEMES or not parsed.netloc:
        raise ConfigError(f"некорректный URL репозитория: {url}")
    if any(char.isspace() for char in url):
        raise ConfigError("URL репозитория содержит пробельные символы")


def validate_file(path):
    file = Path(path)
    if not file.exists():
        raise ConfigError(f"файл тестового репозитория не найден: {path}")
    if not file.is_file():
        raise ConfigError(f"путь не является файлом: {path}")
    try:
        with file.open(encoding="utf-8") as stream:
            stream.read()
    except (OSError, UnicodeDecodeError) as error:
        raise ConfigError(f"не удалось прочитать файл {path}: {error}")


def validate_repo(repo, test_mode):
    if not repo:
        raise ConfigError("репозиторий не задан")
    if test_mode:
        validate_file(repo)
    else:
        validate_url(repo)


def validate_version(version):
    if not version:
        raise ConfigError("версия пакета не задана")
    if not VERSION.match(version):
        raise ConfigError(f"некорректная версия пакета: {version}")


def build_config(package, repo, test_mode, version):
    validate_package(package, test_mode)
    validate_repo(repo, test_mode)
    validate_version(version)
    return Config(package, repo, test_mode, version)
