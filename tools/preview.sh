#!/usr/bin/env bash
#
# preview.sh - render a welcome-message template with SAMPLE data so you can
# check the layout and colours BEFORE committing message.txt. Runs anywhere
# (no root, no system probing - safe on macOS/Linux) and warns about unknown or
# misspelled tokens.
#
#   tools/preview.sh              # previews ./message.txt
#   tools/preview.sh examples/server.txt
#
set -u
FILE=${1:-message.txt}
[ -r "$FILE" ] || { echo "usage: $0 TEMPLATE   (default: message.txt)" >&2; exit 1; }
out=$(cat "$FILE")

# ---- sample values (kept in sync with the renderer's token set) -------------
SOH=$(printf '\001')                          # sentinel marks empty values (see drop below)
sub() { v=$2; [ -n "$v" ] || v=$SOH; out=${out//"{{$1}}"/$v}; }
sub HOSTNAME   "web-01"
sub FQDN       "web-01.example.com"
sub OS         "Ubuntu 24.04.3 LTS"
sub OS_ID      "ubuntu"
sub KERNEL     "6.8.0-71-generic"
sub ARCH       "x86_64"
sub MODEL      "Raspberry Pi 5 Model B Rev 1.0"
sub DATE       "2026-07-03 09:22"
sub TIME       "09:22"
sub TIMEZONE   "UTC"
sub UPTIME     "3 days, 4 hours"
sub BOOTED     "2026-06-29 05:15"
sub CPU        "Intel(R) Xeon(R) CPU E5-2670 v3 @ 2.30GHz"
sub CORES      "4"
sub LOAD       "0.08"
sub LOAD1      "0.08"
sub LOAD5      "0.10"
sub LOAD15     "0.09"
sub CPU_TEMP   "48.3°C"
sub THROTTLED  ""
sub MEMORY     "35%"
sub MEM        "2.7Gi / 7.8Gi"
sub MEM_FREE   "5.1Gi"
sub SWAP       "0B / 2.0Gi"
sub DISK       "19% of 96G"
sub DISK_FREE  "76G"
sub DISK_TOTAL "96G"
sub IP         "192.0.2.10 (ens3), 100.64.0.10 (wt0)"
sub IP4        "192.0.2.10"
sub IPV6       "2001:db8::1"
sub VPNIP      "100.64.0.10"
sub IFACE      "ens3"
sub GATEWAY    "192.0.2.1"
sub DNS        "1.1.1.1, 8.8.8.8"
sub MAC        "52:54:00:ab:cd:ef"
sub PORTS      "22, 80, 443"
sub DOCKER     "3 running (web, api, db)"
sub FAILED     ""
sub USERS      "1"
sub SESSIONS   "2"
sub WHO        "root, admin"
sub REBOOT     "{{RED}}*** System restart required ***{{RESET}}"
sub PUBIP      "203.0.113.45"
sub UPDATES    "42 updates"

# generic {{IP_<IFACE>}} and {{URL_<IFACE>_PORT_<PORT>}} -> sample values
for tok in $(printf '%s' "$out" | grep -oE '\{\{IP_[A-Z0-9]+\}\}' | sort -u); do
    out=${out//"$tok"/"100.64.0.10"}
done
for tok in $(printf '%s' "$out" | grep -oE '\{\{URL_[A-Z0-9]+_PORT_[0-9]+\}\}' | sort -u); do
    prt=$(printf '%s' "$tok" | sed -E 's/^.*_PORT_([0-9]+)\}\}$/\1/')
    case "$prt" in 443) v="https://100.64.0.10" ;; 80) v="http://100.64.0.10" ;; *) v="http://100.64.0.10:$prt" ;; esac
    out=${out//"$tok"/$v}
done

# ---- same sentinel-based empty-line drop as the renderer --------------------
out=$(printf '%s\n' "$out" | awk -v S="$SOH" '
    { p=$0; gsub(/\{\{(RESET|BOLD|DIM|RED|GREEN|YELLOW|BLUE|MAGENTA|CYAN|WHITE)\}\}/,"",p)
      hasS=(index(p,S)>0); gsub(S,"",p)
      if (p ~ /^[[:space:]]*$/) next
      if (hasS && p ~ /:[[:space:]]*$/) next
      line=$0; gsub(S,"",line); print line }')

# ---- warn about leftover (unknown / misspelled) tokens ----------------------
leftover=$(printf '%s' "$out" | grep -oE '\{\{[A-Za-z0-9_]+\}\}' \
    | grep -vE '\{\{(RESET|BOLD|DIM|RED|GREEN|YELLOW|BLUE|MAGENTA|CYAN|WHITE)\}\}' | sort -u || true)

# ---- colours ----------------------------------------------------------------
e=$(printf '\033')
c_reset="${e}[0m";  c_bold="${e}[1m";    c_dim="${e}[2m"
c_red="${e}[31m";   c_green="${e}[32m";  c_yellow="${e}[33m"
c_blue="${e}[34m";  c_magenta="${e}[35m"; c_cyan="${e}[36m"; c_white="${e}[37m"
out=${out//"{{RESET}}"/$c_reset};     out=${out//"{{BOLD}}"/$c_bold};     out=${out//"{{DIM}}"/$c_dim}
out=${out//"{{RED}}"/$c_red};         out=${out//"{{GREEN}}"/$c_green};   out=${out//"{{YELLOW}}"/$c_yellow}
out=${out//"{{BLUE}}"/$c_blue};       out=${out//"{{MAGENTA}}"/$c_magenta};out=${out//"{{CYAN}}"/$c_cyan}
out=${out//"{{WHITE}}"/$c_white}
printf '%s%s\n' "$out" "$c_reset"

if [ -n "$leftover" ]; then
    printf '\n%s[preview] unknown tokens (typos?): %s%s\n' "${e}[33m" "$(printf '%s' "$leftover" | paste -sd' ' -)" "${e}[0m" >&2
    exit 2
fi
