#!/usr/bin/env python3
"""Extract, decode, and normalize a TVBox JSON configuration payload."""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

UPSTREAM_ERROR_EXIT_CODE = 75


class UpstreamPayloadError(Exception):
    """Raised when the upstream endpoint cannot provide a usable payload."""


def main() -> None:
    source_url = os.environ["TVBOX_URL"]
    user_agent = os.environ.get("TVBOX_UA", "okhttp/3.15")
    output_json = Path(os.environ.get("OUT_JSON", "data/tvbox.json"))
    output_meta = Path(os.environ.get("OUT_META", "data/tvbox.meta.json"))

    request = urllib.request.Request(
        source_url,
        headers={
            "User-Agent": user_agent,
            "Accept": "*/*",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw_payload = response.read()
            final_url = response.geturl()
            response_headers = dict(response.headers.items())
    except urllib.error.HTTPError as error:
        raise UpstreamPayloadError(
            f"Upstream endpoint returned HTTP {error.code}."
        ) from error
    except urllib.error.URLError as error:
        raise UpstreamPayloadError(
            f"Could not fetch upstream endpoint: {error.reason}."
        ) from error

    # The endpoint returns a JPEG-like payload to TVBox clients. The actual
    # configuration is appended after the JPEG EOI marker.
    jpeg_eoi_offset = raw_payload.find(b"\xff\xd9")
    if jpeg_eoi_offset < 0:
        raise UpstreamPayloadError("JPEG EOI marker FF D9 was not found.")

    appended_payload = raw_payload[jpeg_eoi_offset + 2 :]

    # The appended section uses a short prefix followed by the "**" separator.
    separator_offset = appended_payload.find(b"**")
    if separator_offset < 0:
        raise UpstreamPayloadError(
            'Payload separator "**" was not found after JPEG EOI.'
        )

    base64_payload = appended_payload[separator_offset + 2 :]
    try:
        decoded_bytes = base64.b64decode(base64_payload, validate=True)
        decoded_text = decoded_bytes.decode("utf-8-sig")
    except (binascii.Error, UnicodeDecodeError) as error:
        raise UpstreamPayloadError("Payload could not be decoded.") from error

    # The upstream configuration may contain JSONC-style full-line comments.
    # This repository stores strict JSON for compatibility with standard tools.
    strict_json_text = "\n".join(
        line
        for line in decoded_text.splitlines()
        if not line.lstrip().startswith("//")
    )

    try:
        parsed_json = json.loads(strict_json_text)
    except json.JSONDecodeError as error:
        raise UpstreamPayloadError("Decoded payload is not valid JSON.") from error

    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_meta.parent.mkdir(parents=True, exist_ok=True)

    output_json.write_text(
        json.dumps(parsed_json, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )

    metadata = {
        "source_url": source_url,
        "final_url": final_url,
        "user_agent": user_agent,
        "raw_size": len(raw_payload),
        "raw_sha256": hashlib.sha256(raw_payload).hexdigest(),
        "decoded_size": len(decoded_bytes),
        "decoded_sha256": hashlib.sha256(decoded_bytes).hexdigest(),
        "json_sha256": hashlib.sha256(output_json.read_bytes()).hexdigest(),
        "jpeg_eoi_offset": jpeg_eoi_offset,
        "appended_size": len(appended_payload),
        "base64_size": len(base64_payload),
        "etag": response_headers.get("ETag"),
        "last_modified": response_headers.get("Last-Modified"),
        "cache_control": response_headers.get("Cache-Control"),
        "content_type": response_headers.get("Content-Type"),
    }

    output_meta.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(json.dumps(metadata, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except UpstreamPayloadError as error:
        print(f"Upstream payload error: {error}", file=sys.stderr)
        raise SystemExit(UPSTREAM_ERROR_EXIT_CODE) from error
