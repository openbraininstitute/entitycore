import hashlib  # noqa: INP001
import json
import logging
import re
from pathlib import Path
from urllib import parse

import click

L = logging.getLogger("extract_traces")

UUID_RE = re.compile(
    r"\b[0-9a-fA-F]{8}-"
    r"[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{12}\b"
)

TIMESTAMP_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z\b")

CHECKSUM_PLACEHOLDERS = {
    "uuid": "__UUID__",
    "timestamp": "__TIMESTAMP__",
    "str": "__STR__",
    "bool": "__BOOL__",
    "number": "__NUMBER__",
}
OUTPUT_PLACEHOLDERS = {
    "uuid": "00000000-0000-4000-8000-000001234678",
    "timestamp": "2025-01-01T00:00:00.000000Z",
}


def normalize(obj, placeholders):  # noqa: PLR0911
    # Replace volatile fields but keep structure
    if isinstance(obj, dict):
        return {k: normalize(v, placeholders) for k, v in obj.items()}
    if isinstance(obj, list):
        return [normalize(v, placeholders) for v in obj]
    if isinstance(obj, str):
        number_of_subs_made = 0
        for pattern, key in (UUID_RE, "uuid"), (TIMESTAMP_RE, "timestamp"):
            obj, count = pattern.subn(placeholders[key], obj)
            number_of_subs_made += count
        if number_of_subs_made > 0:
            return obj
        return placeholders.get("str", obj)
    if isinstance(obj, bool):
        return placeholders.get("bool", obj)
    if isinstance(obj, (int, float)):
        return placeholders.get("number", obj)
    return obj


def compute_checksum(content, length: int) -> str:
    norm = normalize(content, placeholders=CHECKSUM_PLACEHOLDERS)
    raw = json.dumps(norm, sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:length]


def dump_output(content) -> str:
    return json.dumps(
        normalize(content, placeholders=OUTPUT_PLACEHOLDERS),
        sort_keys=True,
        indent=2,
    )


@click.command()
@click.option(
    "--source",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    required=True,
    help="Directory containing the JSON log files.",
)
@click.option(
    "--component",
    type=str,
    default=None,
    help=(
        "Regular expression for URL component (e.g. '^cell-.*'). "
        "If omitted, all components matching 'http://testserver/<comp>' are extracted."
    ),
)
@click.option(
    "--output",
    type=click.Path(file_okay=False, path_type=Path),
    default=Path("extracted"),
    help="Directory to save extracted response JSON.",
)
def extract(source: Path, component: str | None, output: Path) -> None:
    comp_regex = re.compile(component) if component else None
    for path in source.glob("*.json"):
        try:
            data = json.loads(path.read_text())
            request = data["request"]
            response = data["response"]

            if request["method"] not in {"GET", "POST"}:
                # ignore DELETE, PATCH, PUT
                continue
            if response["status_code"] not in {200, 201}:
                # ignore unsuccessful responses
                continue

            parsed_url = parse.urlparse(request["url"])
            head, _, tail = parsed_url.path.strip("/").partition("/")
            if (
                head == "admin"
                or "/assets" in tail
                or "/regions" in tail
                or tail.endswith(("counts", "hierarchy", "derived-from"))
            ):
                # ignore undesired endpoints
                continue
            if comp_regex and not comp_regex.search(head):
                # ignore not matching requests if component has been specified
                continue
            if request["method"] == "POST" and not tail:
                request_type = "one"
            elif not tail:
                request_type = "many"
            elif UUID_RE.fullmatch(tail):
                request_type = "one"
            else:
                L.warning(f"Ignored {request['method']} {parsed_url.path}, skipping {path}")
                continue

            content = dump_output(response["content_json"])
            checksum = compute_checksum(response["content_json"], length=6)

            out_path = output / request_type / head / f"content_{checksum}.json"
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(content)

        except (json.JSONDecodeError, KeyError, TypeError):
            L.warning(f"Malformed json or missing field, skipping {path}")
            continue


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    extract()
