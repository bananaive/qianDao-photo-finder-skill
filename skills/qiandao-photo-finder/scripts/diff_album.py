#!/usr/bin/env python3
"""Compare two verified JSONL album snapshots by stable photo ID."""

import argparse
import datetime as dt
import json
from pathlib import Path
import re

FIELDS = ("filename", "captured_at", "updated_at", "content_sha256")


def read_snapshot(path: Path, count: int) -> dict:
    records = {}
    with path.open(encoding="utf-8") as source:
        for line_no, line in enumerate(source, 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
                if not isinstance(record, dict):
                    raise ValueError("expected a JSON object")
                key = record.get("photo_id")
                if not isinstance(key, str) or not key.strip():
                    raise ValueError("photo_id must be a nonempty string")
                if key in records:
                    raise ValueError("duplicate photo_id")
                fields = {}
                for field in FIELDS:
                    value = record.get(field)
                    if value is None:
                        continue
                    if not isinstance(value, str) or not value.strip():
                        raise ValueError(f"{field} must be a nonempty string")
                    if field in ("captured_at", "updated_at"):
                        try:
                            stamp = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
                        except ValueError:
                            raise ValueError(f"invalid {field}") from None
                        if stamp.utcoffset() is None:
                            raise ValueError(f"{field} requires an explicit timezone")
                        value = stamp.astimezone(dt.timezone.utc).isoformat()
                    elif field == "content_sha256":
                        if not re.fullmatch(r"[a-fA-F0-9]{64}", value):
                            raise ValueError("invalid content_sha256")
                        value = value.lower()
                    fields[field] = value
                records[key] = fields
            except json.JSONDecodeError:
                raise ValueError(f"{path.name}:{line_no}: invalid JSON") from None
            except ValueError as exc:
                raise ValueError(f"{path.name}:{line_no}: {exc}") from None
    if len(records) != count:
        raise ValueError(f"{path.name}: expected {count} unique IDs, found {len(records)}")
    return records


def diff(before: dict, after: dict) -> dict:
    added = [{"photo_id": key, **after[key]} for key in sorted(after.keys() - before.keys())]
    removed = [{"photo_id": key, **before[key]} for key in sorted(before.keys() - after.keys())]
    changed = []
    for key in sorted(before.keys() & after.keys()):
        differences = {
            field: {"before": before[key].get(field), "after": after[key].get(field)}
            for field in FIELDS if before[key].get(field) != after[key].get(field)
        }
        if differences:
            changed.append({"photo_id": key, "fields": differences})
    return {
        "summary": {
            "before": len(before), "after": len(after),
            "added": len(added), "removed": len(removed), "changed": len(changed),
        },
        "added": added,
        "removed": removed,
        "changed": changed,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("before", type=Path)
    parser.add_argument("after", type=Path)
    parser.add_argument("--before-count", required=True, type=int)
    parser.add_argument("--after-count", required=True, type=int)
    parser.add_argument("--output", type=Path, help="New JSON file; otherwise print to stdout.")
    args = parser.parse_args()
    try:
        before = read_snapshot(args.before, args.before_count)
        after = read_snapshot(args.after, args.after_count)
        result = json.dumps(diff(before, after), ensure_ascii=False, indent=2)
        if args.output:
            with args.output.open("x", encoding="utf-8") as dest:
                dest.write(result + "\n")
        else:
            print(result)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"Comparison failed: {exc}\n")


if __name__ == "__main__":
    main()
