#!/usr/bin/env python3
"""Prepare a product repository's AI issue labels without replacing existing labels."""

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys


class SetupError(RuntimeError):
    pass


def api(method, path, payload=None, pages=False):
    argv = ["gh", "api", "--method", method, path]
    if pages:
        argv += ["--paginate", "--slurp"]
    if payload is not None:
        argv += ["--input", "-"]
    try:
        result = subprocess.run(
            argv, input=json.dumps(payload) if payload is not None else None,
            text=True, capture_output=True, timeout=60, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise SetupError("GitHub CLI was unavailable or timed out.") from error
    if result.returncode:
        raise SetupError("GitHub request failed; check login and repository permissions.")
    return json.loads(result.stdout) if result.stdout.strip() else None


def prepare(repository, definitions, apply=False, request=api):
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise SetupError("Use a GitHub repository in OWNER/REPO form.")
    prefix = "repos/" + repository
    repo = request("GET", prefix)
    if not repo.get("has_issues"):
        raise SetupError("Issues are disabled for this repository.")
    pages = request("GET", prefix + "/labels?per_page=100", pages=True)
    existing = {label["name"].casefold() for page in pages for label in page}
    missing = [label for label in definitions if label["name"].casefold() not in existing]
    result = {
        "repository": repo["full_name"],
        "mode": "apply" if apply else "dry-run",
        "missing": [label["name"] for label in missing],
        "preserved": [label["name"] for label in definitions
                      if label["name"].casefold() in existing],
        "created": [],
    }
    if apply and missing:
        permissions = repo.get("permissions", {})
        if not any(permissions.get(key) for key in ("push", "maintain", "admin")):
            raise SetupError("Write permission is required to prepare labels.")
        for label in missing:
            request("POST", prefix + "/labels", label)
            result["created"].append(label["name"])
    # Verify every expected label exists after applying; do not touch issues.
    if apply:
        pages = request("GET", prefix + "/labels?per_page=100", pages=True)
        names = {label["name"].casefold() for page in pages for label in page}
        if any(label["name"].casefold() not in names for label in definitions):
            raise SetupError("Label setup is incomplete; rerun to add missing labels.")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, help="GitHub OWNER/REPO")
    parser.add_argument("--apply", action="store_true", help="Create missing labels")
    args = parser.parse_args(argv)
    definitions = json.loads(
        (Path(__file__).resolve().parents[1] / "assets/issue-labels.json").read_text()
    )
    print(json.dumps(prepare(args.repository, definitions, args.apply), ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except (SetupError, OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
