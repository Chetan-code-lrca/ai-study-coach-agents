#!/usr/bin/env bash
set -euo pipefail

PUSH_TO_ANNA=false
if [[ $# -gt 0 ]]; then
  if [[ "$1" == "--push-to-anna" && $# -eq 1 ]]; then
    PUSH_TO_ANNA=true
  else
    echo "Usage: bash scripts/update-anna-app.sh [--push-to-anna]" >&2
    exit 2
  fi
fi

SCRIPT_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

if ! git rev-parse --show-toplevel >/dev/null 2>&1; then
  echo "Run this script from a Git clone of ai-study-coach-agents." >&2
  exit 1
fi

if [[ -n "$(git status --porcelain)" ]]; then
  echo "Local changes are present. Commit or stash them first; this script will not overwrite them." >&2
  git status --short
  exit 1
fi

echo
echo "[1/8] Updating local main from GitHub..."
git fetch origin main
if git show-ref --verify --quiet refs/heads/main; then
  git switch main
else
  git switch --track -c main origin/main
fi
git pull --ff-only origin main

if ! command -v node >/dev/null 2>&1; then
  echo "Node.js 22 or newer is required." >&2
  exit 1
fi
NODE_MAJOR="$(node -p 'process.versions.node.split(".")[0]')"
if (( NODE_MAJOR < 22 )); then
  echo "Node.js 22 or newer is required; found $(node --version)." >&2
  exit 1
fi
if ! command -v npm >/dev/null 2>&1; then
  echo "npm was not found. Reinstall/enable Node.js and try again." >&2
  exit 1
fi
if ! command -v anna-app >/dev/null 2>&1; then
  echo "Installing the Anna App CLI..."
  npm install --global @anna-ai/cli
fi
if ! command -v anna-app >/dev/null 2>&1; then
  echo "Anna CLI is not on PATH. Restart your terminal and rerun this script." >&2
  exit 1
fi

cd "$REPO_ROOT/anna-app"

echo
echo "[2/8] Installing app dependencies..."
npm install --no-audit --no-fund

echo
echo "[3/8] Building the Anna frontend bundle..."
npm run build

echo
echo "[4/8] Running frontend tests..."
npm test

PYTHON_BIN=""
for candidate in python3 python; do
  if command -v "$candidate" >/dev/null 2>&1; then
    if "$candidate" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)' >/dev/null 2>&1; then
      PYTHON_BIN="$candidate"
      break
    fi
  fi
done
if [[ -z "$PYTHON_BIN" ]]; then
  echo "Python 3.11 or newer was not found; install it and rerun." >&2
  exit 1
fi

echo
echo "[5/8] Running Anna manifest and frontend contract tests..."
"$PYTHON_BIN" -m unittest discover -s tests -v

echo
echo "[6/8] Validating manifest and Host API permissions..."
anna-app validate --strict

echo
echo "[7/8] Checking generated JavaScript syntax..."
node --check bundle/app.js

if [[ "$PUSH_TO_ANNA" == "true" ]]; then
  echo
  echo "Checking Anna account login..."
  if ! anna-app whoami; then
    echo "Anna CLI is not logged in. Run: anna-app login --host https://anna.partners" >&2
    exit 1
  fi

  echo
  echo "[8/8] Pushing the validated bundle to Anna's working draft..."
  anna-app apps push
  echo
  echo "Anna working draft updated. This is not a public release."
  echo "Open https://anna.partners/developer, install/test the draft, then cut version 0.1.2 and complete the platform review/publish steps."
else
  echo
  echo "All local build and validation checks passed."
  echo "After local checks pass, rerun: bash scripts/update-anna-app.sh --push-to-anna"
fi
