#!/usr/bin/env python3
"""Validate data/*.json against the endpoint schema."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
SCHEMA_FILE = ROOT / "schemas" / "endpoint.schema.json"


def main() -> int:
    schema = json.loads(SCHEMA_FILE.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)

    errors: list[str] = []
    total = 0
    per_file: dict[str, int] = {}

    for path in sorted(DATA_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            errors.append(f"{path.name}: root must be a JSON array")
            continue

        per_file[path.name] = len(data)
        for index, endpoint in enumerate(data):
            total += 1
            for err in validator.iter_errors(endpoint):
                errors.append(f"{path.name}[{index}] ({endpoint.get('name', '?')}): {err.message}")

    if errors:
        for message in errors:
            print(message, file=sys.stderr)
        print(f"\nValidation failed with {len(errors)} error(s).", file=sys.stderr)
        return 1

    print(f"Validated {total} endpoints across {len(per_file)} files.")
    for name, count in per_file.items():
        print(f"  {name}: {count}")
    print("Update **Catalog snapshot:** in README.md if you changed the data files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
