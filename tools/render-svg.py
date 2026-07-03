#!/usr/bin/env python3
"""Render a welcome-message template to an SVG "screenshot".

Mirrors the renderer in setup.sh: substitutes {{TOKENS}} with sample values,
drops label lines whose value is empty (colour-token aware), and turns the
{{COLOUR}} tokens into styled text. Output is a terminal-window SVG suitable
for embedding in the README.

Usage: tools/render-svg.py examples/server.txt docs/img/server.svg
"""
import html
import re
import sys

# Sample values matching the Ubuntu box from the README example (kept in sync
# with tools/preview.sh and the renderer's token set).
SAMPLE = {
    "HOSTNAME": "web-01",
    "FQDN": "web-01.example.com",
    "OS": "Ubuntu 24.04.3 LTS", "OS_ID": "ubuntu",
    "KERNEL": "6.8.0-71-generic", "ARCH": "x86_64",
    "MODEL": "Raspberry Pi 5 Model B Rev 1.0",
    "DATE": "2026-07-03 09:22", "TIME": "09:22", "TIMEZONE": "UTC",
    "UPTIME": "3 days, 4 hours", "BOOTED": "2026-06-29 05:15",
    "CPU": "Intel(R) Xeon(R) CPU E5-2670 v3 @ 2.30GHz", "CORES": "4",
    "LOAD": "0.08", "LOAD1": "0.08", "LOAD5": "0.10", "LOAD15": "0.09",
    "CPU_TEMP": "48.3°C", "THROTTLED": "",
    "MEMORY": "35%", "MEM": "2.7Gi / 7.8Gi", "MEM_FREE": "5.1Gi", "SWAP": "0B / 2.0Gi",
    "DISK": "19% of 96G", "DISK_FREE": "76G", "DISK_TOTAL": "96G",
    "IP": "192.0.2.10 (ens3), 100.64.0.10 (wt0)", "IP4": "192.0.2.10",
    "IPV6": "2001:db8::1", "VPNIP": "100.64.0.10",
    "IFACE": "ens3", "GATEWAY": "192.0.2.1", "DNS": "1.1.1.1, 8.8.8.8",
    "MAC": "52:54:00:ab:cd:ef", "PORTS": "22, 80, 443",
    "DOCKER": "3 running (web, api, db)", "FAILED": "",
    "USERS": "1", "SESSIONS": "2", "WHO": "root, admin",
    "PUBIP": "203.0.113.45", "UPDATES": "42 updates",
    # The renderer wraps a pending reboot in red; reproduce that here.
    "REBOOT": "{{RED}}*** System restart required ***{{RESET}}",
}


def substitute_generic(text):
    """Resolve {{IP_<IFACE>}} and {{URL_<IFACE>_PORT_<PORT>}} with sample values."""
    text = re.sub(r"\{\{IP_[A-Z0-9]+\}\}", "100.64.0.10", text)

    def _url(m):
        port, ip = m.group(1), "100.64.0.10"
        if port == "443":
            return "https://" + ip
        if port == "80":
            return "http://" + ip
        return f"http://{ip}:{port}"

    return re.sub(r"\{\{URL_[A-Z0-9]+_PORT_([0-9]+)\}\}", _url, text)

COLOURS = {
    "RESET": None, "BOLD": "bold", "DIM": "dim",
    "RED": "#ff6b6b", "GREEN": "#5af78e", "YELLOW": "#f1fa8c",
    "BLUE": "#6cb6ff", "MAGENTA": "#ff6ac1", "CYAN": "#8be9fd", "WHITE": "#f8f8f2",
}
DEFAULT_FG = "#c9d1d9"
COLOUR_RE = re.compile(r"\{\{(" + "|".join(COLOURS) + r")\}\}")
ANY_COLOUR_RE = re.compile(r"\{\{(?:" + "|".join(COLOURS) + r")\}\}")

CHAR_W = 8.4      # px per monospace char (the grid; textLength pins runs to it)
FONT = 14
LINE_H = 20
PAD = 16
TITLE_H = 28


SENTINEL = "\x01"  # marks empty values so only token-empty lines drop (see renderer)


def substitute_data(text):
    for name, val in SAMPLE.items():
        text = text.replace("{{" + name + "}}", val if val else SENTINEL)
    return text


def drop_empty_lines(text):
    out = []
    for line in text.split("\n"):
        probe = ANY_COLOUR_RE.sub("", line)
        has_s = SENTINEL in probe
        probe = probe.replace(SENTINEL, "")
        if probe.strip() == "":
            continue
        if has_s and re.search(r":\s*$", probe):
            continue
        out.append(line.replace(SENTINEL, ""))
    return out


def line_to_runs(line):
    """Yield (text, fg, bold, dim) runs, tracking colour state across tokens."""
    runs, fg, bold, dim, pos = [], DEFAULT_FG, False, False, 0
    for m in COLOUR_RE.finditer(line):
        if m.start() > pos:
            runs.append((line[pos:m.start()], fg, bold, dim))
        tok = m.group(1)
        if tok == "RESET":
            fg, bold, dim = DEFAULT_FG, False, False
        elif tok == "BOLD":
            bold = True
        elif tok == "DIM":
            dim = True
        else:
            fg = COLOURS[tok]
        pos = m.end()
    if pos < len(line):
        runs.append((line[pos:], fg, bold, dim))
    return runs


def render(template_path, svg_path, verbatim=False):
    with open(template_path, encoding="utf-8") as fh:
        text = fh.read()
    text = substitute_generic(substitute_data(text))
    if verbatim:   # keep blank lines (for UI mockups like the menu)
        lines = [ln.replace(SENTINEL, "") for ln in text.split("\n")]
        while lines and lines[-1].strip() == "":
            lines.pop()
    else:
        lines = drop_empty_lines(text)
    parsed = [line_to_runs(ln) for ln in lines]

    width_chars = max((sum(len(t) for t, *_ in runs) for runs in parsed), default=1)
    w = int(width_chars * CHAR_W + 2 * PAD)
    h = int(TITLE_H + len(lines) * LINE_H + 2 * PAD)

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,'
        f'&quot;DejaVu Sans Mono&quot;,&quot;Liberation Mono&quot;,monospace" font-size="{FONT}">',
        f'<rect width="{w}" height="{h}" rx="8" fill="#0d1117"/>',
        f'<rect width="{w}" height="{TITLE_H}" rx="8" fill="#161b22"/>',
        f'<rect y="{TITLE_H-8}" width="{w}" height="8" fill="#161b22"/>',
        '<circle cx="16" cy="14" r="5.5" fill="#ff5f56"/>',
        '<circle cx="34" cy="14" r="5.5" fill="#ffbd2e"/>',
        '<circle cx="52" cy="14" r="5.5" fill="#27c93f"/>',
    ]
    # Each run is pinned to an explicit column (x) and forced to an exact width
    # (textLength) so the grid holds regardless of the viewer's font.
    y = TITLE_H + PAD + FONT
    for runs in parsed:
        out.append(f'<text y="{y}" xml:space="preserve">')
        col = 0
        for txt, fg, bold, dim in runs:
            if txt == "":
                continue
            x = PAD + col * CHAR_W
            tl = len(txt) * CHAR_W
            style = f' fill="{fg}"'
            if bold:
                style += ' font-weight="700"'
            if dim:
                style += ' opacity="0.6"'
            out.append(
                f'<tspan x="{x:.1f}" textLength="{tl:.1f}" lengthAdjust="spacingAndGlyphs"'
                f'{style}>{html.escape(txt)}</tspan>'
            )
            col += len(txt)
        out.append("</text>")
        y += LINE_H
    out.append("</svg>")

    with open(svg_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")
    print(f"wrote {svg_path}  ({w}x{h}, {len(lines)} lines)")


if __name__ == "__main__":
    _args = [a for a in sys.argv[1:] if a != "--verbatim"]
    render(_args[0], _args[1], verbatim="--verbatim" in sys.argv)
