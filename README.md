# terminal-welcome-message

A custom login banner (MOTD) for Linux hosts, driven by a template in this repo.
Edit [`message.txt`](message.txt) on GitHub and every host that ran the installer
picks up the new **layout** automatically — while filling in **live, per-host
values** (IP, uptime, temperature, listening ports, reboot status …) locally at
display time.

Shows on **SSH login**, **local console login**, and **desktop terminal windows**,
and always reads a **local** copy, so it works even when the host is offline.

<p align="center">
  <img src="docs/img/server.svg" alt="Server banner: host info, IP, temperature, ports, updates, reboot notice" width="460">
</p>

Ships with ready-to-use templates in [`examples/`](examples/) — copy one into
`message.txt` to adopt it:

| Example | Preview |
|---------|---------|
| [`server.txt`](examples/server.txt) — full system summary | <img src="docs/img/server.svg" alt="server example" width="340"> |
| [`branded.txt`](examples/branded.txt) — coloured header + service link | <img src="docs/img/branded.svg" alt="branded example" width="340"> |
| [`ascii-art.txt`](examples/ascii-art.txt) — ASCII art + colour | <img src="docs/img/ascii-art.svg" alt="ascii-art example" width="280"> |
| [`minimal.txt`](examples/minimal.txt) — hostname + IP | — |
| [`plain.txt`](examples/plain.txt) — one static line | — |

## Install

Runnable as-is on Raspberry Pi OS / Debian / Ubuntu / Fedora / RHEL / Arch:

```bash
curl -fsSL https://raw.githubusercontent.com/Carlboms-Data-AB/terminal-welcome-message/main/setup.sh | sudo bash
```

| Option | Default | Meaning |
|--------|---------|---------|
| `--interval MINUTES` | `15` | how often to re-sync the template (1–59) |
| `--branch NAME` | `main` | which branch to fetch `message.txt` from |
| `--url URL` | — | fetch the template from a custom URL (self-host / staging) |
| `--uninstall` | — | undo the install and restore the box |

```bash
curl -fsSL .../setup.sh | sudo bash -s -- --interval 10          # sync every 10 min
curl -fsSL .../setup.sh | sudo bash -s -- --uninstall            # remove
```

## Editing the banner

`message.txt` is a template. Static text is shown as-is; `{{TOKENS}}` are
replaced on each host with that host's live values. **A line whose token comes
out empty is omitted** — so the reboot line only appears when a reboot is
pending, the swap line only when swap exists, etc.

**Preview before you ship** with the bundled tool (runs anywhere — Mac or Linux,
no root — using sample data, and flags typos):

```bash
tools/preview.sh                 # preview ./message.txt
tools/preview.sh examples/server.txt
```

Test on a single host before touching everyone with `--url` / `--branch`:

```bash
# point one box at a work-in-progress branch, verify, then merge to main
curl -fsSL .../setup.sh | sudo bash -s -- --branch my-edit
```

### Token catalogue

<details open><summary><b>System</b></summary>

| Token | Value |
|-------|-------|
| `{{HOSTNAME}}` | short hostname |
| `{{FQDN}}` | fully-qualified name (no DNS lookup) |
| `{{OS}}` | distro name + version (e.g. `Ubuntu 24.04.3 LTS`) |
| `{{OS_ID}}` | distro id (`debian`, `fedora`, `arch`, …) |
| `{{KERNEL}}` | kernel release |
| `{{ARCH}}` | CPU architecture (`x86_64`, `aarch64`) |
| `{{MODEL}}` | hardware model (Raspberry Pi model / DMI product) |
</details>

<details><summary><b>Time</b></summary>

| Token | Value |
|-------|-------|
| `{{DATE}}` | `YYYY-MM-DD HH:MM` |
| `{{TIME}}` | `HH:MM` |
| `{{TIMEZONE}}` | IANA timezone |
| `{{UPTIME}}` | pretty uptime |
| `{{BOOTED}}` | boot timestamp |
</details>

<details><summary><b>CPU</b></summary>

| Token | Value |
|-------|-------|
| `{{CPU}}` | CPU / SoC model |
| `{{CORES}}` | logical CPU count |
| `{{LOAD}}` / `{{LOAD1}}` | 1-minute load average |
| `{{LOAD5}}` / `{{LOAD15}}` | 5- / 15-minute load |
| `{{CPU_TEMP}}` | CPU temperature |
| `{{THROTTLED}}` | Raspberry Pi throttling state (yellow, hidden when OK) |
</details>

<details><summary><b>Memory & disk</b></summary>

| Token | Value |
|-------|-------|
| `{{MEMORY}}` | memory used, `%` |
| `{{MEM}}` | used / total (e.g. `2.7Gi / 7.8Gi`) |
| `{{MEM_FREE}}` | available memory |
| `{{SWAP}}` | swap used / total (hidden when no swap) |
| `{{DISK}}` | root usage (e.g. `19% of 96G`) |
| `{{DISK_FREE}}` / `{{DISK_TOTAL}}` | free / total on `/` |
</details>

<details><summary><b>Network</b></summary>

| Token | Value |
|-------|-------|
| `{{IP}}` | all global IPv4 with interface |
| `{{IP4}}` | primary IPv4 (default route) |
| `{{IPV6}}` | primary global IPv6 |
| `{{VPNIP}}` | VPN/overlay address (auto-detects NetBird `wt0`/`netbird` or `100.64.0.0/10`) |
| `{{IFACE}}` | default-route interface |
| `{{GATEWAY}}` | default gateway |
| `{{DNS}}` | resolvers |
| `{{MAC}}` | MAC of the default interface |
| `{{PORTS}}` | listening TCP ports reachable off-box |
</details>

<details><summary><b>Services, sessions & status</b></summary>

| Token | Value |
|-------|-------|
| `{{DOCKER}}` | running container count + names (docker/podman) |
| `{{FAILED}}` | failed systemd units (yellow, hidden when none) |
| `{{USERS}}` / `{{SESSIONS}}` | logged-in users / active sessions |
| `{{WHO}}` | list of logged-in users |
| `{{REBOOT}}` | `*** System restart required ***` in red when pending |
| `{{PUBIP}}` | public IP — *cached* by the timer (offline-safe) |
| `{{UPDATES}}` | pending package updates — *cached* by the timer |
</details>

<details><summary><b>Generic (build your own)</b></summary>

Parameterised tokens resolved from whatever you write — no hardcoded apps:

| Token | Value |
|-------|-------|
| `{{IP_<IFACE>}}` | that interface's IPv4, e.g. `{{IP_ETH0}}`, `{{IP_WG0}}` |
| `{{URL_<IFACE>_PORT_<PORT>}}` | clickable URL to a service on that interface — e.g. `{{URL_WG0_PORT_80}}` → `http://<wg0-ip>`, `{{URL_ETH0_PORT_443}}` → `https://<eth0-ip>` (port 443 → `https`, 80 → `http`, else `http://ip:port`) |

Example: a CasaOS dashboard reachable over your NetBird interface is just
`{{URL_WT0_PORT_80}}`.
</details>

### Colour & styling

Wrap text in colour tokens; `{{RESET}}` returns to default (auto-appended at the
end). Colours are applied **locally** after sanitising, so they never travel from
GitHub. Emoji work too (they're UTF-8).

`{{RED}}` `{{GREEN}}` `{{YELLOW}}` `{{BLUE}}` `{{MAGENTA}}` `{{CYAN}}` `{{WHITE}}` `{{BOLD}}` `{{DIM}}` `{{RESET}}`

## How it works

- **Login path (local, offline-safe).** On Debian/Ubuntu the banner is rendered
  at each login by `/etc/update-motd.d/00-welcome`, so values are always current;
  the stock banner/ad scripts are disabled so ours replaces them. On other distros
  the banner is rendered onto `/etc/motd` on the timer.
- **Desktop terminal windows** (non-login shells `pam_motd` never covers) render
  live via a guarded `/etc/profile.d` snippet.
- **Sync path (background).** A systemd timer (cron fallback) fetches the template
  text, strips escape sequences, and refreshes cached values (public IP, update
  counts). If GitHub is unreachable the last template stays in place.

## Security

Only the template **text** is fetched — never executable code. The renderer is
installed **once, locally**, and treats the template as **data**: tokens are
string-substituted, the template is **never executed** (no `eval`), and it's
stripped of escape sequences before display. So even a compromised repo can only
change banner text — not run code, even though the render runs as root at login.

## Making it your own (forking)

The engine is generic. To run your own copy:

- Point hosts at your template with `--url https://…/message.txt` (no fork
  needed), **or** fork and change `REPO_RAW` at the top of `setup.sh`.
- Everything installed uses neutral names (`terminal-welcome-*`, `00-welcome`),
  so nothing is tied to this org except the default `message.txt` text and the
  example branding — edit those to taste.

## Known edge cases

- **`Last login:` line.** On SSH, `sshd` prints `Last login: …` above the banner
  (it's separate from the MOTD). Suppress per-user with `touch ~/.hushlogin`, or
  globally with `PrintLastLog no` in `/etc/ssh/sshd_config`.
- **Text vs logic.** Editing `message.txt` propagates automatically. Changing the
  renderer *logic* (new tokens, `setup.sh`) does **not** — re-run the installer on
  each host (it's idempotent).
- **Desktop terminals** are covered for `bash` only; shells inside `tmux`/`screen`
  don't repeat the banner, and `sudo -s` inside SSH can print it twice.
- **Minimal installs** (Fedora/Arch without `iproute2`/`procps`) leave some tokens
  blank; the installer warns which tools are missing.

## Files

| File | Role |
|------|------|
| `setup.sh` | installer / uninstaller; embeds the renderer, updater, shell snippet, timer/cron |
| `message.txt` | the banner **template** — edit this to change what hosts show |
| `examples/` | ready-to-use templates |
| `tools/preview.sh` | render a template with sample data (preview before deploying) |
| `tools/render-svg.py` | generate the README screenshots from a template |
