# P05 tag-push false-negative recovery

- UTC: 20260929T023746Z
- HEAD/origin before recovery: `463161b247d165c7c410f486683ac8c1c58fb72d`
- freeze tag: `wp2-e2e-smoke-eng-v22-freeze-2026-09-29`
- freeze commit: `85d0bb75107bc49cec32ad7d453b37fb44c80be8`
- freeze verification: PASS
- v2.2 scientific outcomes before recovery: NONE
- root cause: controller used `git push origin main --tags`; two unrelated historical local tags conflicted with already-existing canonical remote tags.
- intended v2.2 freeze tag was already present remotely and correct.
- old local conflicting tag objects preserved under `refs/archive/v22-prepush-tag-conflicts/`.
- local historical tag refs aligned to origin; remote historical tags were not moved.
- P05 marked PASS only after all postconditions were independently verified.
- no kit/scientific code changed; no model/API call made.

```json
{
  "incident": "P05_TAG_PUSH_FALSE_NEGATIVE",
  "utc": "20260929T023746Z",
  "head_before": "463161b247d165c7c410f486683ac8c1c58fb72d",
  "origin_main_before": "463161b247d165c7c410f486683ac8c1c58fb72d",
  "freeze_tag": "wp2-e2e-smoke-eng-v22-freeze-2026-09-29",
  "freeze_commit": "85d0bb75107bc49cec32ad7d453b37fb44c80be8",
  "freeze_verify": "PASS",
  "conflicts": {
    "stagec-djangocms-study-wiring-verified-01": {
      "old_local_tag_object": "35dd6681d98ff51549d9f75a57fe896bdf02f605",
      "old_local_peeled_commit": "35dd6681d98ff51549d9f75a57fe896bdf02f605",
      "remote_canonical_peeled_commit": "39f7b3bad558fb4752b935b64fcbcc7a353f0d83",
      "archive_ref": "refs/archive/v22-prepush-tag-conflicts/stagec-djangocms-study-wiring-verified-01-20260929T023746Z",
      "new_local_peeled_commit": "39f7b3bad558fb4752b935b64fcbcc7a353f0d83"
    },
    "v0.9.6-pilot-exec-ready": {
      "old_local_tag_object": "db26f33617f2323954a721da28864a69edd40356",
      "old_local_peeled_commit": "db26f33617f2323954a721da28864a69edd40356",
      "remote_canonical_peeled_commit": "af9b47444fafac260d887dabbe4e3ddc3b22a00f",
      "archive_ref": "refs/archive/v22-prepush-tag-conflicts/v0.9.6-pilot-exec-ready-20260929T023746Z",
      "new_local_peeled_commit": "af9b47444fafac260d887dabbe4e3ddc3b22a00f"
    }
  }
}
```
