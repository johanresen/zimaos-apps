# ZimaHomelab Apps

A small third-party app store for ZimaOS and CasaOS. Same packaging model as
[BigBearCasaOS](https://github.com/bigbeartechworld/big-bear-casaos): one directory per
app under `Apps/`, a `docker-compose.yml` carrying an `x-casaos` metadata block, and a
README that tells a human what to do after the install button.

## Apps

| App | Description | Port |
|---|---|---|
| [Mattermost](Apps/mattermost) | Self-hosted team chat with PostgreSQL, threads, files, bots | 8065 |
| [Mattermost (8067)](Apps/mattermost-8067) | Same app on host port 8067, for running alongside an existing install | 8067 |

## Add this store to ZimaOS

A v2 store is consumed as a generated `store.json`, not as a bare repository. After the
first CI run publishes the `gh-pages` branch, the source URL is:

```
https://cdn.jsdelivr.net/gh/johanresen/zimaos-apps@gh-pages/store.json
```

1. **App Store → ⋯ (top right) → Add app source** (older builds: *Add third-party store*).
2. Paste that `store.json` URL.
3. Save, refresh the App Store — the apps appear in their own section.

CasaOS: **App Store → More apps → Add source**, same URL.

Until CI has run once there is no `store.json`. To install a single app immediately,
skip the store entirely: **App Store → Install a custom app**, paste the contents of
`Apps/<app>/docker-compose.yml`.

## Layout

```
Apps/
  mattermost/
    docker-compose.yml   # services + x-casaos metadata
    README.md            # post-install instructions, backup, troubleshooting
    icon.svg             # store icon (source URL is rewritten at build time)
```

## Packaging rules this repo follows

- Top-level `name:` is `big-bear-<app>`-style (`big-bear-mattermost`), and
  `x-casaos.id` is reverse-domain (`com.zimahomelab.mattermost`) — the directory name is
  not the identity.
- `x-casaos.port_map` is a **quoted string**, and `main` names the user-facing web
  service, never a database.
- All persistent state lives under `/DATA/AppData/$AppID/...` so it survives reinstalls
  and can be backed up by hand.
- Secrets have working defaults and are documented in the app README, so a fresh install
  never boots into a broken state.
- A one-shot `permissions` service fixes volume ownership before the app starts. Bind
  mounts created by the installer are root-owned; images that run unprivileged crash
  without this, and it's the most common reason a store app "works for the author".
- Metadata is authored in `x-casaos` only. Per-service `x-casaos` blocks are legacy and
  are stripped by the v2 build pipeline, so nothing depends on them.
- Every compose file must pass `docker compose config -q`:

  ```bash
  cd Apps/mattermost && AppID=mattermost docker compose config -q
  ```

  (`AppID` is substituted at install time by the store, so set it for local validation.)

## Versioning

`x-casaos.version` tracks the **app** version, not the store. Bump `update_at` and fill
`release_notes` on every change so the store can show a changelog.

## Licence

Packaging: MIT. Each app keeps its upstream licence — see the app README.
