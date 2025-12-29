
#!/usr/bin/env bash
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/gm-tts-repo.tar.gz"
echo "Creating tarball $OUT"
tar -czf "$OUT" -C "$ROOT" frontend backend README.md
echo "Done"
