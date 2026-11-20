#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

if [[ ! -f .env ]]; then
    echo "Missing .env. Copy the existing panel configuration here before updating." >&2
    exit 1
fi

if [[ "$(git branch --show-current)" != "dev" ]]; then
    echo "This updater must run from the dev branch." >&2
    exit 1
fi

origin_url="$(git remote get-url origin)"
case "${origin_url,,}" in
    *github.com/kjjyjkjhgnynjy-design/panel*|*github.com:kjjyjkjhgnynjy-design/panel*) ;;
    *)
        echo "The origin remote must point to kjjyjkjhgnynjy-design/panel." >&2
        exit 1
        ;;
esac

git pull --ff-only origin dev
docker compose up -d --build pasarguard
docker compose ps pasarguard
