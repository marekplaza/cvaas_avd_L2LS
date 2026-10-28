#!/usr/bin/env bash
# BUM duplicate test across the DCI.
#
# Each series flushes the dynamic MACs on every switch, so the first packets are flooded
# as unknown unicast, then pings FW2 (DC2) from FW1 (DC1) on every stretched VLAN and
# counts duplicate replies. With a DF mismatch between the gateways (see check_df.sh)
# most series show +10..+15 duplicates; with matching DFs 0 or an occasional +1.
#
# Changes state: clears the MAC address tables (relearned within seconds).
#
# Usage: dup_test.sh [rounds]   (default 3, i.e. 12 series of 5 pings)
set -uo pipefail
ROUNDS=${1:-3}
TARGETS="10.1.10.12 10.2.10.12 10.3.10.12 10.3.99.12"
SWITCHES=$(docker ps --format '{{.Names}}' | grep -E 'marpla-dc-[12]-(s0|wew|priv|ext)' | sort)
total=0 lost=0

echo "== BUM duplicate test, $(date -u +%Y-%m-%dT%H:%M:%SZ), rounds=$ROUNDS"
for r in $(seq 1 "$ROUNDS"); do
    for ip in $TARGETS; do
        for s in $SWITCHES; do docker exec "$s" Cli -p 15 -c "clear mac address-table dynamic" >/dev/null 2>&1 & done
        wait
        res=$(docker exec marpla-dc-1-fw01 Cli -p 15 -c "ping $ip repeat 5 interval 0.2" | grep "packets transmitted")
        dups=$(grep -oE '\+[0-9]+ duplicates' <<<"$res" | grep -oE '[0-9]+' || true)
        grep -q ' 0% packet loss' <<<"$res" || lost=$((lost + 1))
        total=$((total + ${dups:-0}))
        printf '  %s round %s  %-11s dups=%-3s %s\n' "$(date -u +%H:%M:%SZ)" "$r" "$ip" "${dups:-0}" "$res"
    done
done

echo
echo "dup_test: $total duplicate(s), $lost series with loss"
