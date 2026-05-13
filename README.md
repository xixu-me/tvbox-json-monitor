# TVBox JSON Monitor

This repository automatically monitors a TVBox-compatible endpoint, extracts the hidden configuration payload, decodes it, normalizes it as strict JSON, and commits updates when changes are detected.

The update process is handled by GitHub Actions on a scheduled basis.

## What this repository does

The monitored endpoint returns a JPEG-like payload for TVBox-style clients.

The actual TVBox configuration is embedded after the JPEG end marker:

1. Request the endpoint with a TVBox-like `User-Agent`.
2. Locate the JPEG EOI marker: `FF D9`.
3. Read the appended payload after the JPEG data.
4. Locate the `**` separator.
5. Base64-decode the content after the separator.
6. Normalize the decoded configuration into strict JSON.
7. Commit the updated JSON files when changes are detected.

## Output files

The workflow maintains the following generated files:

```text
data/tvbox.json
data/tvbox.meta.json
```

### `data/tvbox.json`

This is the decoded TVBox configuration, normalized as strict JSON.

The upstream configuration may contain JSONC-style full-line comments. These comments are removed so that the stored file can be parsed by standard JSON tools.

### `data/tvbox.meta.json`

This file contains metadata about the latest decoded payload, including:

```text
source_url
final_url
user_agent
raw_size
raw_sha256
decoded_size
decoded_sha256
json_sha256
jpeg_eoi_offset
appended_size
base64_size
etag
last_modified
cache_control
content_type
```

## GitHub Actions workflow

The workflow runs automatically every 5 minutes:

```yaml
- cron: "*/5 * * * *"
```

It can also be triggered manually from the GitHub Actions UI using `workflow_dispatch`.

GitHub-hosted scheduled workflows are not guaranteed to run exactly on time. They may be delayed depending on GitHub Actions load.

## Repository variable

The monitored endpoint URL is configured through a GitHub Actions repository variable.

Create the following repository variable:

```text
Name: TVBOX_URL
Value: https://www.xn--sss604efuw.com/tv/
```

The URL should preferably include the trailing slash to avoid unnecessary redirects.

To set it:

```text
Repository
→ Settings
→ Secrets and variables
→ Actions
→ Variables
→ New repository variable
```

## Required repository settings

The workflow commits generated files back to the repository.

Make sure GitHub Actions has write permission:

```text
Repository
→ Settings
→ Actions
→ General
→ Workflow permissions
→ Read and write permissions
```

## Commit behavior

If the decoded JSON has not changed, the workflow exits without creating a commit.

If changes are detected, the workflow commits the updated files with a message like:

```text
chore(tvbox): update decoded JSON 2026-05-13T16:00:00Z
```

## File normalization

The generated `data/tvbox.json` is not a byte-for-byte copy of the decoded upstream payload.

It is normalized for public repository use:

- Full-line `//` comments are removed.
- JSON is parsed and re-serialized.
- UTF-8 characters are preserved.
- Output formatting uses 2-space indentation.
- Object key order is preserved as parsed by Python.

This makes the file easier to diff, inspect, and consume with standard JSON tooling.

## Security and privacy

The endpoint URL is stored as a repository variable, not a secret.

This is intentional because the URL is not sensitive and this repository is designed for public use.

No credentials are required beyond the default `GITHUB_TOKEN` provided by GitHub Actions.

## Local extraction

The same extraction logic can be run locally with Python:

```bash
export TVBOX_URL="https://www.xn--sss604efuw.com/tv/"
export TVBOX_UA="okhttp/3.15"
export OUT_JSON="data/tvbox.json"
export OUT_META="data/tvbox.meta.json"

python3 scripts/extract_tvbox.py
```

## Disclaimer

This repository only monitors, decodes, normalizes, and stores configuration data from the configured endpoint.

It does not host video content, proxy media streams, or provide any playback service.
