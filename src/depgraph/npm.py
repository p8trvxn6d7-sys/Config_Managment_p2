import json
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from depgraph.errors import RepoError
from depgraph.semver import max_satisfying

HTTP_NOT_FOUND = 404
TIMEOUT_SECONDS = 10
JSON_ACCEPT = "application/json"
ABBREVIATED_ACCEPT = (
    "application/vnd.npm.install-v1+json; q=1.0, "
    "application/json; q=0.8, */*"
)
DOCUMENT_FIELDS = ("versions", "dist-tags")


def build_package_url(repo, package):
    base = repo.rstrip("/")
    return f"{base}/{quote(package, safe='@')}"


def build_url(repo, package, version):
    return f"{build_package_url(repo, package)}/{quote(version)}"


def fetch_json(url, accept=JSON_ACCEPT):
    request = Request(url, headers={"Accept": accept})
    try:
        with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            return json.load(response)
    except HTTPError as error:
        if error.code == HTTP_NOT_FOUND:
            raise RepoError(f"пакет или версия не найдены: {url}")
        raise RepoError(f"ошибка HTTP {error.code}: {url}")
    except URLError as error:
        raise RepoError(f"не удалось подключиться: {error.reason}")
    except ValueError:
        raise RepoError(f"репозиторий вернул некорректный JSON: {url}")
    except OSError as error:
        raise RepoError(f"ошибка при получении данных: {error}")


def extract_dependencies(data):
    if not isinstance(data, dict):
        raise RepoError("неожиданный формат ответа репозитория")
    dependencies = data.get("dependencies", {})
    if not isinstance(dependencies, dict):
        raise RepoError("поле dependencies имеет неожиданный формат")
    return {str(name): str(spec) for name, spec in dependencies.items()}


def fetch_dependencies(repo, package, version):
    data = fetch_json(build_url(repo, package, version))
    return extract_dependencies(data)


def fetch_document(repo, package):
    url = build_package_url(repo, package)
    data = fetch_json(url, ABBREVIATED_ACCEPT)
    if not isinstance(data, dict):
        raise RepoError("неожиданный формат ответа репозитория")
    for field in DOCUMENT_FIELDS:
        if not isinstance(data.get(field, {}), dict):
            raise RepoError(f"поле {field} имеет неожиданный формат")
    return data


def is_deprecated(manifest):
    return isinstance(manifest, dict) and bool(manifest.get("deprecated"))


def pick_latest(tags, versions, spec):
    latest = tags.get("latest")
    if latest in versions and max_satisfying([latest], spec) == latest:
        return str(latest)
    return None


def pick_preferred(versions, spec):
    active = [
        name for name, manifest in versions.items()
        if not is_deprecated(manifest)
    ]
    return max_satisfying(active, spec) or max_satisfying(list(versions), spec)


def pick_version(document, package, spec):
    tags = document.get("dist-tags", {})
    if spec in tags:
        return str(tags[spec])
    versions = document.get("versions", {})
    found = pick_latest(tags, versions, spec) or pick_preferred(versions, spec)
    if found is None:
        raise RepoError(
            f"у пакета {package} нет версии, подходящей под {spec!r}"
        )
    return found


class NpmSource:
    def __init__(self, repo):
        self.repo = repo
        self.documents = {}

    def document(self, package):
        if package not in self.documents:
            self.documents[package] = fetch_document(self.repo, package)
        return self.documents[package]

    def resolve(self, package, spec):
        return pick_version(self.document(package), package, spec)

    def dependencies(self, package, version):
        versions = self.document(package).get("versions", {})
        if version not in versions:
            raise RepoError(f"версия {package}@{version} не найдена")
        return extract_dependencies(versions[version])
