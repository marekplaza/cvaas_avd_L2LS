#!/usr/bin/env bash
# Data-plane test from both firewall cluster nodes (cEOS hosts).
#
# For every zone (ext, wew, priv) each FW node pings:
#   - the anycast gateway on the stretched FW VLAN       (local leaf pair)
#   - the other FW node on the stretched FW VLAN         (L2 across the DCI via the EVPN gateways)
#   - the anycast gateway on its DC-local VLAN           (local leaf pair)
# plus the other FW node on the HA VLAN 399              (pure L2 across the DCI).
#
# Exit code is non-zero when any target does not answer.
set -uo pipefail

declare -A ZONE_OCTET=([ext]=1 [wew]=2 [priv]=3)
declare -A ZONE_VLAN=([ext]=110 [wew]=210 [priv]=310)
fails=0

ping_from() { # ping_from <fw> <target> <label>
    local out received
    out=$(docker exec "$1" Cli -p 15 -c "ping $2 repeat 3 timeout 2" 2>&1)
    received=$(grep -oE '[0-9]+ received' <<<"$out" | grep -oE '^[0-9]+')
    if [ "${received:-0}" -gt 0 ]; then
        printf '  PASS  %-15s %s\n' "$2" "$3"
    else
        printf '  FAIL  %-15s %s\n' "$2" "$3"
        fails=$((fails + 1))
    fi
}

for dc in 1 2; do
    fw=marpla-dc-$dc-fw01
    me=$((10 + dc)); peer=$((13 - dc))
    if ! docker inspect -f '{{.State.Running}}' "$fw" 2>/dev/null | grep -q true; then
        echo "== $fw is not running"; fails=$((fails + 1)); continue
    fi
    echo "== $fw (DC$dc, .$me)"
    for zone in ext wew priv; do
        o=${ZONE_OCTET[$zone]} v=${ZONE_VLAN[$zone]}
        ping_from "$fw" "10.$o.10.1"     "$zone: anycast GW, VLAN $v (stretched)"
        ping_from "$fw" "10.$o.10.$peer" "$zone: FW node in DC$((3 - dc)) across DCI, VLAN $v"
        ping_from "$fw" "10.$o.2$dc.1"   "$zone: anycast GW, VLAN ${v:0:1}2$dc (DC$dc local)"
    done
    ping_from "$fw" "10.3.99.$peer" "priv: FW HA peer across DCI, VLAN 399 (L2 only)"
done

echo
if [ "$fails" -eq 0 ]; then echo "fw_test: all targets reachable"; else echo "fw_test: $fails target(s) unreachable"; fi
exit $((fails > 0))
