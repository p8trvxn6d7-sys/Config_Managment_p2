import operator
import re

from depgraph.errors import RepoError

PART = r"(x|X|\*|\d+)"
VERSION = re.compile(
    r"^v?(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z.-]+))?(?:\+[0-9A-Za-z.-]+)?$"
)
PARTIAL = re.compile(
    rf"^[v=]*{PART}(?:\.{PART})?(?:\.{PART})?"
    r"(?:-([0-9A-Za-z.-]+))?(?:\+[0-9A-Za-z.-]+)?$"
)
OPERATOR = re.compile(r"^(>=|<=|>|<|=|\^|~>?)?(.*)$")
GLUE = re.compile(r"(>=|<=|>|<|=|\^|~>?)\s+")
HYPHEN = " - "
WILDCARDS = ("x", "X", "*")
FULL = 3
TILDE_WIDTH = 2
PARTIAL_GROUPS = 3
PRE_GROUP = 4
STABLE = (1, ())
LOWEST = (0, ())
NOTHING = (0, 0, 0, LOWEST)
COMPARE = {
    ">=": operator.ge,
    ">": operator.gt,
    "<=": operator.le,
    "<": operator.lt,
    "=": operator.eq,
}


def pre_key(text):
    if not text:
        return STABLE
    ids = tuple(
        (0, int(item), "") if item.isdigit() else (1, 0, item)
        for item in text.split(".")
    )
    return (0, ids)


def parse_version(text):
    match = VERSION.match(text)
    if not match:
        return None
    major, minor, patch, pre = match.groups()
    return (int(major), int(minor), int(patch), pre_key(pre))


def parse_partial(text):
    match = PARTIAL.match(text)
    if not match:
        raise RepoError(f"неподдерживаемая спецификация версии: {text}")
    parts = []
    for group in match.groups()[:PARTIAL_GROUPS]:
        if group is None or group in WILDCARDS:
            break
        parts.append(int(group))
    return parts, match.group(PRE_GROUP)


def pad(parts):
    return (list(parts) + [0] * FULL)[:FULL]


def bumped(parts):
    return parts[:-1] + [parts[-1] + 1]


def low_key(parts, pre):
    return (*pad(parts), pre_key(pre))


def high_key(parts, index):
    return (*pad(bumped(parts[:index + 1])), LOWEST)


def range_of(parts, pre, index):
    return [(">=", low_key(parts, pre)), ("<", high_key(parts, index))]


def caret(parts, pre):
    if not parts:
        return []
    index = next((i for i, v in enumerate(parts) if v), len(parts) - 1)
    return range_of(parts, pre, index)


def tilde(parts, pre):
    if not parts:
        return []
    return range_of(parts, pre, min(len(parts), TILDE_WIDTH) - 1)


def plain(parts, pre):
    if len(parts) == FULL:
        return [("=", low_key(parts, pre))]
    if not parts:
        return []
    return range_of(parts, pre, len(parts) - 1)


def at_least(parts, pre):
    return [(">=", low_key(parts, pre))]


def greater(parts, pre):
    if len(parts) == FULL:
        return [(">", low_key(parts, pre))]
    if not parts:
        return [("<", NOTHING)]
    return [(">=", (*pad(bumped(parts)), STABLE))]


def less(parts, pre):
    if not parts:
        return [("<", NOTHING)]
    suffix = pre_key(pre) if pre else LOWEST
    return [("<", (*pad(parts), suffix))]


def at_most(parts, pre):
    if len(parts) == FULL:
        return [("<=", low_key(parts, pre))]
    if not parts:
        return []
    return [("<", high_key(parts, len(parts) - 1))]


HANDLERS = {
    "^": caret,
    "~": tilde,
    "~>": tilde,
    "": plain,
    "=": plain,
    ">=": at_least,
    ">": greater,
    "<": less,
    "<=": at_most,
}


def parse_comparator(token):
    match = OPERATOR.match(token)
    parts, pre = parse_partial(match.group(2))
    return HANDLERS[match.group(1) or ""](parts, pre)


def parse_hyphen(text):
    low, high = text.split(HYPHEN, 1)
    low_parts, low_pre = parse_partial(low.strip())
    high_parts, high_pre = parse_partial(high.strip())
    return at_least(low_parts, low_pre) + at_most(high_parts, high_pre)


def parse_set(text):
    text = text.strip()
    if HYPHEN in text:
        return parse_hyphen(text)
    comparators = []
    for token in GLUE.sub(r"\1", text).split():
        comparators.extend(parse_comparator(token))
    return comparators


def parse_range(spec):
    return [parse_set(part) for part in spec.split("||")]


def matches(key, comparators):
    return all(COMPARE[op](key, bound) for op, bound in comparators)


def max_satisfying(versions, spec):
    sets = parse_range(spec)
    stable = []
    unstable = []
    for text in versions:
        key = parse_version(text)
        if key is None or not any(matches(key, item) for item in sets):
            continue
        (stable if key[-1] == STABLE else unstable).append((key, text))
    pool = stable or unstable
    return max(pool)[1] if pool else None
