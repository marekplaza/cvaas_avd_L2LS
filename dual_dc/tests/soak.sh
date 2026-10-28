#!/usr/bin/env bash
# Soak test: traffic across the DCI under MAC churn, then count BFD flaps.
#
# For <minutes>, in a loop: flush the dynamic MACs on all switches, then 20 pings from
# FW1 (DC1) to FW2 (DC2) on VLAN 310. The many parallel docker exec calls are also the
# host load that exposed too tight BFD timers on the lab host (see README, BFD flaps).
# At the end: BFD "Up to Down" events per device since the start, ping summary and
# the highest BFD Rx interval seen on a leaf and a gateway.
#
# Changes state: clears the MAC address tables (relearned within seconds).
#
# Usage: soak.sh [minutes] [target]   (default 10, 10.3.10.12)
# Exit code is non-zero when any BFD session went down or any series lost packets.
set -uo pipefail
MIN=${1:-10}
TARGET=${2:-10.3.10.12}
SWITCHES=$(docker ps --format '{{.Names}}' | grep -E 'marpla-dc-[12]-(s0|wew|priv|ext)' | sort)

bfd_downs() { docker exec "$1" Cli -p 15 -c "show logging" 2>/dev/null | grep -c 'BFD-5-STATE_CHANGE.*Up to Down'; }

declare -A before
for s in $SWITCHES; do before[$s]=$(bfd_downs "$s"); done

echo "== soak $MIN min, FW1 -> $TARGET, start $(date -u +%H:%M:%SZ)"
log=$(mktemp)
end=$(($(date +%s) + MIN * 60))
while [ "$(date +%s)" -lt "$end" ]; do
    for s in $SWITCHES; do docker exec "$s" Cli -p 15 -c "clear mac address-table dynamic" >/dev/null 2>&1 & done
    wait
    docker exec marpla-dc-1-fw01 Cli -p 15 -c "ping $TARGET repeat 20 interval 0.2" |
        grep transmitted | sed "s/^/$(date -u +%H:%M:%S) /" | tee -a "$log"
done

echo
echo "== BFD Up->Down since start"
flaps=0
for s in $SWITCHES; do
    n=$(($(bfd_downs "$s") - ${before[$s]}))
    [ "$n" -lt 0 ] && n="?"   # log buffer wrapped
    printf '  %-22s %s\n' "$s" "$n"
    [ "$n" != 0 ] && flaps=$((flaps + 1))
done

echo "== ping series: $(wc -l <"$log")"
awk '{print $6, $7}' "$log" | sed 's/,$//' | sort | uniq -c | sed 's/^/  /'
lossy=$(grep -vc ' 0% packet loss' "$log")

echo "== max BFD Rx interval (since last reset)"
for h in marpla-dc-1-priv-l03 marpla-dc-1-s01; do
    docker exec "$h" Cli -p 15 -c "show bfd peers detail" |
        awk -v h="$h" '/Rx Interval/ {split($8, a, "/"); if (a[2] + 0 > m) m = a[2] + 0} END {printf "  %-22s %s ms\n", h, m}'
done
rm -f "$log"

echo
echo "soak: $flaps device(s) with BFD flaps, $lossy series with loss"
exit $(((flaps + lossy) > 0))
