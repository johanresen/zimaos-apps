#!/usr/bin/env python3
"""Validate store packages under Apps/ against the ZimaOS/CasaOS x-casaos contract.

    python3 scripts/validate.py            # check every app
    python3 scripts/validate.py Apps/x     # check one

Exits non-zero on error; warnings do not fail the run.
"""
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("pyyaml required: pip install pyyaml")

REQUIRED = ["id", "main", "index", "port_map", "icon", "title", "category", "version"]
RECOMMENDED = ["tagline", "description", "author", "developer", "architectures"]
LOCALIZED = ["title", "tagline", "description"]
ID_RE = re.compile(r"^[a-z0-9._-]+$")

errors, warnings = [], []


def err(app, msg):
    errors.append(f"{app}: {msg}")


def warn(app, msg):
    warnings.append(f"{app}: {msg}")


def check(app_dir: Path):
    app = app_dir.name
    cf = app_dir / "docker-compose.yml"
    if not cf.is_file():
        return err(app, "docker-compose.yml missing")
    try:
        doc = yaml.safe_load(cf.read_text())
    except yaml.YAMLError as exc:
        return err(app, f"YAML does not parse: {exc}")

    if not isinstance(doc, dict):
        return err(app, "compose is not a mapping")
    for key in ("name", "services", "x-casaos"):
        if key not in doc:
            err(app, f"top-level '{key}' missing")
    if errors:
        return

    services = doc["services"] or {}
    meta = doc["x-casaos"] or {}

    for key in REQUIRED:
        if key not in meta:
            err(app, f"x-casaos.{key} missing")
    for key in RECOMMENDED:
        if key not in meta:
            warn(app, f"x-casaos.{key} missing (recommended)")

    app_id = str(meta.get("id", ""))
    if app_id:
        if not ID_RE.match(app_id):
            err(app, f"x-casaos.id '{app_id}' has illegal characters")
        if len([s for s in app_id.split(".") if s]) < 2:
            err(app, f"x-casaos.id '{app_id}' must be reverse-domain (two+ segments)")
        if app_id != app_id.lower():
            err(app, "x-casaos.id must be lowercase")

    main = meta.get("main")
    if main and main not in services:
        err(app, f"x-casaos.main '{main}' is not a service in this file")

    pm = meta.get("port_map")
    if pm is not None and not isinstance(pm, str):
        err(app, "x-casaos.port_map must be a quoted string (\"8065\"), not a number")
    elif isinstance(pm, str) and not pm.isdigit():
        err(app, f"x-casaos.port_map '{pm}' should be numeric")

    for key in LOCALIZED:
        val = meta.get(key)
        if isinstance(val, dict) and "en_US" not in val:
            err(app, f"x-casaos.{key} is localized but has no en_US entry")

    icon = meta.get("icon")
    if isinstance(icon, str) and not icon.startswith(("http://", "https://")):
        if not (app_dir / icon).is_file():
            err(app, f"x-casaos.icon '{icon}' not found in {app_dir}")

    # volumes must be AppData-backed and containers must not be privileged
    for sname, svc in services.items():
        if not isinstance(svc, dict):
            continue
        if svc.get("privileged") is True:
            warn(app, f"service '{sname}' runs privileged")
        for vol in svc.get("volumes") or []:
            src = vol.split(":")[0] if isinstance(vol, str) else vol.get("source", "")
            if not str(src).startswith("/DATA/AppData/$AppID"):
                warn(app, f"service '{sname}' volume '{src}' is not under /DATA/AppData/$AppID")
        if "ports" not in svc and sname == main:
            err(app, f"main service '{sname}' publishes no ports")

    # every published port should be documented somewhere
    if not (app_dir / "README.md").is_file():
        warn(app, "README.md missing")


def main():
    root = Path(__file__).resolve().parent.parent
    apps = [Path(a) for a in sys.argv[1:]] or sorted((root / "Apps").iterdir())
    checked = 0
    for d in apps:
        if d.is_dir():
            before = len(errors)
            check(d)
            checked += 1
            if len(errors) == before:
                print(f"  ok    {d.name}")

    for w in warnings:
        print(f"  warn  {w}")
    for e in errors:
        print(f"  FAIL  {e}")
    print(f"\n{checked} app(s) checked — {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
