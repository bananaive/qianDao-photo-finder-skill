# Snapshot comparison

Use one manifest per album category and snapshot. Verify the category in the page or export; an album-wide count and a category count are different scopes. Use the site's stable photo identifier rather than its filename or a signed download URL. Keep raw URLs and credentials in task-local storage and out of any shared index or repository.

Each JSONL line is an object with a nonempty string `photo_id`. Optional comparison fields are `filename`, `captured_at`, `updated_at`, and `content_sha256`. Timestamps are ISO 8601 with an explicit offset. The content hash is for the same image rendition in both snapshots. Source links and preview paths may exist in private manifests; the comparison script ignores and omits them.

For a paginated source, record the published count and version before and after reading the pages when available. Confirm that the last page was reached, the unique ID count matches the published count, and the version stayed stable. Count the older snapshot from its recorded verified count. If the version changes, refresh and compare one consistent snapshot. With only a partial export, describe the coverage rather than declaring that no photos were added.

From the repository root, run the synthetic example:

```sh
python3 skills/qiandao-photo-finder/scripts/diff_album.py \
  examples/before.jsonl examples/after.jsonl --before-count 3 --after-count 3
```

The counts are verified expectations, not the number of lines you happened to fetch. The example produces one addition, one removal, and one changed record despite identical totals. For incremental screening, inspect added IDs and any changed records that may have a new image. A changed metadata field is not proof that pixels changed. If an ID and its metadata are unchanged, this check cannot detect a silent image replacement; a comparable content hash can.

Keep the original baseline until the new snapshot has been verified. Retain a review record of confirmed and rejected IDs and apply it to each refresh.
