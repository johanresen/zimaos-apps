# Mattermost (8067)

Self-hosted team messaging for ZimaOS / CasaOS, packaged as a store app.

Mattermost Team Edition is an open-source alternative to Slack and Discord. This app
bundles the server with PostgreSQL, fixes volume ownership on first install, and keeps
everything under `AppData`, so it upgrades and backs up like any other store app.

## What you get

| | |
|---|---|
| Web UI | `http://<your-nas-ip>:8065` |
| Database | PostgreSQL 16, private to the app network |
| Data | `/DATA/AppData/mattermost/` |
| RAM | ~700 MB idle, 1.5–2 GB with history |
| Disk | image ~600 MB, data grows with uploads |

Features: channels and DMs, threads, file and image sharing, full-text search, slash
commands, incoming/outgoing webhooks, bot accounts, and mobile push through Mattermost's
push proxy.

## Install

From the store: install Mattermost and open it.

Manual, without a store source:

```bash
cd /DATA/AppData
git clone <this-repo> zimaos-apps
cd zimaos-apps/Apps/mattermost
docker compose up -d
```

Or paste this app's `docker-compose.yml` into **App Store → Install a custom app**.

## First run

1. Open `http://<nas-ip>:8065` and **create the first account — it becomes System Admin**.
2. System Console → **Site Configuration → Site URL**: enter the exact address you use in
   the browser, port included. This is not cosmetic — WebSockets and push deep links are
   validated against it, and a mismatch shows as "connection lost".
3. System Console → **Environment → Push Notification Server**: enable, then set
   *Push Notification Contents* to `Generic description with only sender name` if you don't
   want message text passing through the push proxy.
4. Optional: System Console → **Integrations → Bot Accounts** to let Hermes or any other
   bot talk to your workspace.

Migrations run on first start and take 30–90 seconds. Restarting before they finish makes
it look broken; give it two minutes.

## Change the database password

`changeme-mattermost-db` appears twice in `docker-compose.yml` — once under `database`
(`POSTGRES_PASSWORD`) and once inside `MM_SQLSETTINGS_DATASOURCE`. Change both to the same
value **before** first start, or afterwards with:

```bash
docker exec -it big-bear-mattermost-database psql -U mmuser -d mattermost \
  -c "ALTER USER mmuser WITH PASSWORD 'new-password';"
```

then update the compose file and `docker compose up -d`.

## Backup

Everything that matters is in two places:

- `/DATA/AppData/mattermost/database` — the Postgres cluster (users, posts, channels)
- `/DATA/AppData/mattermost/data` — uploaded files

Stop the stack first for a consistent copy:

```bash
docker compose down
sudo tar czf mattermost-backup-$(date +%F).tar.gz -C /DATA/AppData mattermost
docker compose up -d
```

`config/` holds `config.json` (settings) and the server's signing keys. Losing `database`
or `config` means recreating every account.

## Upgrade

```bash
cd /DATA/AppData/zimaos-apps/Apps/mattermost
docker compose pull
docker compose up -d
```

Mattermost upgrades databases forward automatically but **not backward** — snapshot the
backup above before a major version bump.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Crash loop, `permission denied ... config.json` | volume owned by root | the `mm-permissions` service handles it; if it was skipped, `sudo chown -R 2000:2000 /DATA/AppData/mattermost` |
| `connection lost` banner, no live updates | Site URL mismatch | set it to the exact browser address |
| Web UI loads, login fails right after install | migrations still running | wait, then retry |
| No mobile notifications | push disabled server-side, or Doze | enable in System Console, set app battery to Unrestricted |
| Port 8065 already in use | another Mattermost/container | change the host port in `ports:` and set Site URL to match |
| `database ... does not exist` | Postgres volume from a different install | remove `/DATA/AppData/mattermost/database` for a clean start (destroys data) |

## Notes

- No TLS and no end-to-end encryption. Put it behind a reverse proxy (Nginx Proxy Manager,
  Caddy, Traefik) if it will leave your LAN, and set Site URL to the HTTPS address.
- The official mobile apps need HTTPS for reliable operation on iOS; Android accepts plain
  HTTP on a LAN.
- Not affiliated with Mattermost, Inc. Mattermost is a trademark of Mattermost, Inc.
  Licensed under the Mattermost Team Edition licence; this packaging is MIT.

## Port

This entry publishes **8067** on purpose, so it can run alongside the
8065 install. Set the Site URL to `http://<host-ip>:8067` in the first-run
wizard — otherwise websockets and push deep links point at the wrong port.
