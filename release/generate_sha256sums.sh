#!/usr/bin/env bash
# Regenerate release/SHA256SUMS.txt.
#
# Policy: this file is a release/tag-time provenance artifact, not a
# continuously-maintained checksum of the working tree. Do not regenerate it
# on every ordinary commit -- only when cutting a release candidate or tag,
# so that SHA256SUMS.txt corresponds to a specific, citable release state.
#
# Usage: bash release/generate_sha256sums.sh
set -eu

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT"

OUT="release/SHA256SUMS.txt"
TMP="$(mktemp)"

{
  echo "# SHA-256 checksums of committed PDP Control Framework files."
  echo "# Generated at release/tag time only -- see release/generate_sha256sums.sh."
  echo "# Regenerate with: bash release/generate_sha256sums.sh"
  echo "#"
  echo "# Verify with: (cd <repo-root> && sha256sum -c release/SHA256SUMS.txt --ignore-missing)"
} > "$TMP"

git ls-files -z \
  | grep -z -v '^release/SHA256SUMS.txt$' \
  | sort -z \
  | xargs -0 sha256sum >> "$TMP"

mv "$TMP" "$OUT"
echo "Wrote $OUT"
