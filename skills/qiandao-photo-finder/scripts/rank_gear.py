#!/usr/bin/env python3
"""Rank local equipment crops using a local DINOv2 model."""

import argparse
from collections import defaultdict
import json
import math
from pathlib import Path


def load_rows(path):
    root = path.resolve().parent
    rows = []
    seen = set()
    with path.open(encoding="utf-8") as source:
        for line_no, line in enumerate(source, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
                if not isinstance(row, dict):
                    raise ValueError("expected an object")
                for key in ("photo_id", "subject_id", "image"):
                    if not isinstance(row.get(key), str) or not row[key].strip():
                        raise ValueError(f"{key} must be a nonempty string")
                key = (row["photo_id"], row["subject_id"])
                if key in seen:
                    raise ValueError("duplicate photo_id and subject_id pair")
                seen.add(key)
                image = Path(row["image"])
                resolved = (root / image).resolve()
                if image.is_absolute() or not resolved.is_relative_to(root):
                    raise ValueError("image must be a relative path inside the manifest directory")
                regions = row.get("regions")
                if not isinstance(regions, dict):
                    raise ValueError("regions must be an object")
                for name, box in regions.items():
                    if not name.strip() or not isinstance(box, list) or len(box) != 4:
                        raise ValueError("each region must be a named box with four coordinates")
                    if any(type(x) is not int or x < 0 for x in box):
                        raise ValueError("box coordinates must be nonnegative integers")
                    if box[2] <= box[0] or box[3] <= box[1]:
                        raise ValueError("box has no area")
                rows.append((key, resolved, regions))
            except (ValueError, TypeError) as exc:
                raise ValueError(f"{path.name}:{line_no}: {exc}") from None
    return rows


def parse_weights(text, gear):
    if text is None:
        return dict.fromkeys(sorted(gear), 1.0)
    weights = {}
    for value in text.split(","):
        name, sep, raw = value.partition("=")
        if not sep or name not in gear or name in weights:
            raise ValueError("weights must name unique gear with valid reference crops")
        weight = float(raw)
        if not math.isfinite(weight) or weight <= 0:
            raise ValueError("weights must be finite and positive")
        weights[name] = weight
    return weights


def run(args):
    from PIL import Image, ImageOps
    import torch
    from transformers import AutoImageProcessor, AutoModel

    references = load_rows(args.references)
    candidates = load_rows(args.candidates)
    if not args.model.is_dir():
        raise ValueError("--model must be a local DINOv2 model directory")
    processor = AutoImageProcessor.from_pretrained(
        str(args.model), local_files_only=True, trust_remote_code=False
    )
    model = AutoModel.from_pretrained(
        str(args.model), local_files_only=True, trust_remote_code=False
    ).eval()

    def regions(rows, wanted=None):
        for key, path, boxes in rows:
            if not boxes or (wanted is not None and not wanted.intersection(boxes)):
                continue
            with Image.open(path) as original:
                image = ImageOps.exif_transpose(original).convert("RGB")
            for name, (left, top, right, bottom) in boxes.items():
                if wanted is not None and name not in wanted:
                    continue
                if right > image.width or bottom > image.height:
                    raise ValueError(f"region {name!r} exceeds image bounds: {path.name}")
                if min(right - left, bottom - top) < args.min_size:
                    continue
                crop = image.crop((left, top, right, bottom))
                yield key, name, ImageOps.pad(crop, (224, 224), color=(127, 127, 127))

    def embeddings(items):
        batch = []
        for item in items:
            batch.append(item)
            if len(batch) == args.batch_size:
                yield from encode(batch)
                batch.clear()
        if batch:
            yield from encode(batch)

    def encode(batch):
        inputs = processor(images=[item[2] for item in batch], return_tensors="pt")
        with torch.inference_mode():
            vectors = model(**inputs).last_hidden_state[:, 0, :]
            vectors = torch.nn.functional.normalize(vectors, dim=-1)
        for (key, name, _), vector in zip(batch, vectors):
            yield key, name, vector

    prototypes = defaultdict(list)
    for _, name, vector in embeddings(regions(references)):
        prototypes[name].append(vector)
    if not prototypes:
        raise ValueError("no usable reference crops")
    weights = parse_weights(args.weights, prototypes.keys())
    matrix = {name: torch.stack(prototypes[name]) for name in weights}
    evidence = defaultdict(dict)
    for key, name, vector in embeddings(regions(candidates, set(weights))):
        evidence[key][name] = float((matrix[name] @ vector).max().item())
    results = []
    total_weight = sum(weights.values())
    for key, _, _ in candidates:
        details = evidence[key]
        observed = sum(weights[name] for name in details)
        coverage = observed / total_weight
        similarity = sum(weights[name] * value for name, value in details.items()) / observed if observed else None
        score = 0.85 * ((similarity + 1) / 2) + 0.15 * coverage if similarity is not None else None
        results.append({
            "photo_id": key[0], "subject_id": key[1],
            "score": round(score, 6) if score is not None else None,
            "coverage": round(coverage, 6),
            "gear_similarity": {name: round(value, 6) for name, value in details.items()},
        })
    results.sort(key=lambda row: -(row["score"] if row["score"] is not None else -1))
    with args.output.open("x", encoding="utf-8") as dest:
        for row in results:
            dest.write(json.dumps(row, ensure_ascii=False) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("references", type=Path)
    parser.add_argument("candidates", type=Path)
    parser.add_argument("--model", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--weights", help="Comma-separated gear=weight pairs; defaults to equal weights.")
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--min-size", type=int, default=8, help="Minimum crop width and height, in pixels.")
    args = parser.parse_args()
    if args.batch_size < 1 or args.min_size < 1:
        parser.error("batch size and minimum crop size must be positive")
    if args.output.exists():
        parser.error("output already exists")
    try:
        run(args)
    except (ImportError, OSError, ValueError) as exc:
        parser.exit(1, f"Ranking failed: {exc}\n")


if __name__ == "__main__":
    main()
