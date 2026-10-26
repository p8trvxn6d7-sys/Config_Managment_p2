import json
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from depgraph.errors import RepoError

HTTP_NOT_FOUND = 404
TIMEOUT_SECONDS = 10


def build_url(repo, package, version):
    base = repo.rstrip("/")
    return f"{base}/{quote(package, safe='@')}/{quote(version)}"


def fetch_json(url):
    request = Request(url, headers={"Accept": "application/json"})
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
