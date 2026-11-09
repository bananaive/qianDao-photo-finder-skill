# Photo screening and review

## OCR and visual evidence

- Use a readable rendition for bib OCR; verify against a known example downscaled to the same size. If the full frame fails and the bib is visible, crop around the number and retry. Keep leading zeros and match the complete token. Treat OCR hits as candidates and inspect them visually; unrelated signs, overlays, and bibs on other riders can also produce hits.
- On macOS, put one local image path per line in a text file. Run `swift skills/qiandao-photo-finder/scripts/scan-bibs.swift 0427 /path/to/local-images.txt fast` with a synthetic bib replaced by the requested number. The output is JSONL with match paths and a coverage summary. Try `accurate` on a smaller subset when worthwhile. Where Apple Vision is unavailable, use a local OCR tool and follow the same verification steps.
- Read small previews for triage; fetch better renditions for ambiguous details. Budget by measuring a sample, then batch the download and keep the needed copies. Do not treat a score or a missing match as an exhaustive result.

## Optional gear ranking

Use a local object detector, pose landmarks, or manual boxes to locate the equipment. Crop tight around **the gear or clothing**, keeping backgrounds, bare faces, and adjacent riders outside the regions. For a group image, make one record per subject and associate that subject's bike and bib with that same record. Do not use facial descriptors or face embeddings.

Provide two JSONL files in separate local directories, one for confirmed reference crops and one for candidate crops. Paths are relative to each file. Each record has `photo_id`, `subject_id`, `image`, and `regions` with named pixel boxes in `[left, top, right, bottom]` order on the EXIF-oriented image. Right and bottom are exclusive. Example with synthetic data:

```json
{"photo_id":"sample-07","subject_id":"rider-1","image":"previews/sample-07.jpg","regions":{"helmet":[160,42,219,82],"visor":[165,73,214,82],"shorts":[153,185,226,258],"bike":[107,230,301,408]}}
```

Use the same gear names in the references and candidates. In a Python environment with Pillow, PyTorch and Transformers, provision a DINOv2 model locally first, then run:

```sh
python3 skills/qiandao-photo-finder/scripts/rank_gear.py references.jsonl candidates.jsonl \
  --model /path/to/local-dinov2-model --weights helmet=2,visor=2,shorts=2,bike=3 \
  --output ranked.jsonl
```

The helper runs offline against the specified model and does not run any code from the model directory. It reports per-gear similarity, coverage, and a ranking score, not an identity prediction. Give intermittently worn gear a lower weight, keep a fallback for hidden gear, and watch out for one strong feature compensating for an obvious contradiction. A fresh helmet color may be useful as a clue only when associated with the intended rider rather than another subject or the background. Check a known match and a few known non-matches before scaling the run.

## Review and delivery

Prefer a small set of verified results over a long score list. A photo next to a confirmed frame may show another rider. Use the crop to locate a candidate, then check the full image for the same rider, gear, bike, readable number, and requested viewpoint. If a required detail is unclear, label it unconfirmed or omit it when the user wants only clear photos.

For mobile review, provide inline pictures and stable photo page links where supported. Local HTML with relative assets may appear as code or miss its images on another device. Keep original-sized downloads, review previews, and index records separate. Do not include a private album URL, original photos, cached datasets, credentials, location, or user-specific examples in reusable code or docs.
