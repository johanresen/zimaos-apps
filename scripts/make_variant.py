#!/usr/bin/env python3
"""Generate a port-pinned variant of an app from its base package.

ZimaOS links an app tile using the store's `port_map`, so running a second copy
on another host port needs its own app entry — not just a different mapping —
or the tile opens the wrong port.

    python3 scripts/make_variant.py Apps/mattermost 8067

Writes Apps/<base>-<port>/ with docker-compose.yml, README.md and icon.svg.
Re-run it after editing the base app; the variant is a build artifact, not a fork.
"""
from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

BASE_NAME = "big-bear-mattermost"
BASE_PORT = "8065"
BASE_APP_ID = "com.zimahomelab.mattermost"
BASE_NETWORK = "big_bear_mattermost_network"


def generate(base: Path, host_port: str) -> Path:
    suffix = f"-{host_port}"
    src = (base / "docker-compose.yml").read_text()
    text = src

    # project name (top-level `name:`) and every container_name
    text = re.sub(rf"^name: {BASE_NAME}$", f"name: {BASE_NAME}{suffix}", text, flags=re.M)
    text = text.replace(f"container_name: {BASE_NAME}-database", f"container_name: {BASE_NAME}-database{suffix}")
    text = text.replace(f"container_name: {BASE_NAME}-permissions", f"container_name: {BASE_NAME}-permissions{suffix}")
    text = text.replace(f"container_name: {BASE_NAME}\n", f"container_name: {BASE_NAME}{suffix}\n")

    # isolated network
    text = text.replace(BASE_NETWORK, f"big_bear_mattermost_{host_port}_network")

    # host port only — the container still listens on 8065 internally
    text = text.replace(f"- {BASE_PORT}:{BASE_PORT}", f"- {host_port}:{BASE_PORT}")

    # store identity
    text = text.replace(f"id: {BASE_APP_ID}", f"id: {BASE_APP_ID}-{host_port}")
    text = text.replace(f'port_map: "{BASE_PORT}"', f'port_map: "{host_port}"')
    text = text.replace("title:\n    en_US: Mattermost", f"title:\n    en_US: Mattermost ({host_port})")

    out = ROOT / "Apps" / f"{base.name}{suffix}"
    out.mkdir(parents=True, exist_ok=True)
    header = (
        f"# Generated from Apps/{base.name} by scripts/make_variant.py — do not edit by hand.\n"
        f"# Identical to the base app, published on host port {host_port}.\n"
    )
    (out / "docker-compose.yml").write_text(header + text)

    shutil.copy2(base / "icon.svg", out / "icon.svg")

    readme = (base / "README.md").read_text()
    readme = readme.replace(
        "Mattermost",
        f"Mattermost ({host_port})",
        1,
    )
    readme += (
        f"\n## Port\n\nThis entry publishes **{host_port}** on purpose, so it can run alongside the\n"
        f"{BASE_PORT} install. Set the Site URL to `http://<host-ip>:{host_port}` in the first-run\n"
        "wizard — otherwise websockets and push deep links point at the wrong port.\n"
    )
    (out / "README.md").write_text(readme)

    return out


if __name__ == "__main__":
    if len(sys.argv) != 3 or not sys.argv[2].isdigit():
        sys.exit("usage: make_variant.py Apps/<app> <host-port>")
    base = (ROOT / sys.argv[1]).resolve()
    if not (base / "docker-compose.yml").is_file():
        sys.exit(f"no docker-compose.yml in {base}")
    written = generate(base, sys.argv[2])
    print(f"wrote {written.relative_to(ROOT)}")
