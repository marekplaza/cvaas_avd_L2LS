#!/usr/bin/env bash
# Read-only check of the I-ESI DF election on the EVPN gateways (spines).
#
# Both gateways of a DC must elect the same DF for every stretched VLAN. When they
# disagree, both forward BUM traffic into the DCI and the far side gets duplicates.
# They only agree when they see each other's type-1/type-4 routes, i.e. when the
# local iBGP EVPN session between them is up (branch single-domain-gw-ibgp).
#
# Usage: check_df.sh [label]
#   label - also save the detailed show output to tests/results/<label>/
# Exit code is non-zero on a DF mismatch.
set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
VLANS="110 210 310 399"
fails=0

cli() { timeout 60 docker exec "$1" Cli -p 15 -c "$2" 2>&1; }

df_of() { # df_of <gateway> <vlan>
    cli "$1" "show bgp evpn instance vlan $2" | awk '/^ *Designated forwarder/ {print $3}'
}

echo "== DF per stretched VLAN"
for dc in 1 2; do
    for v in $VLANS; do
        a=$(df_of marpla-dc-$dc-s01 "$v")
        b=$(df_of marpla-dc-$dc-s02 "$v")
        if [ -n "$a" ] && [ "$a" = "$b" ]; then st=OK; else st=MISMATCH; fails=$((fails + 1)); fi
        printf '  DC%s VLAN %-4s s01 DF=%-12s s02 DF=%-12s %s\n' "$dc" "$v" "${a:--}" "${b:--}" "$st"
    done
done

echo "== Local gateway iBGP EVPN session"
for dc in 1 2; do
    for s in 1 2; do
        peer=10.10$dc.0.$((3 - s))
        state=$(cli marpla-dc-$dc-s0$s "show bgp neighbors $peer" | awk -F', *' '/BGP state is/ {sub(/.*BGP state is /, "", $0); print $1; exit}')
        printf '  marpla-dc-%s-s0%s -> %-11s %s\n' "$dc" "$s" "$peer" "${state:-not configured}"
    done
done

if [ -n "${1:-}" ]; then
    out=$HERE/results/$1
    mkdir -p "$out"
    for dc in 1 2; do
        for s in 1 2; do
            h=marpla-dc-$dc-s0$s
            for cmd in "show bgp evpn instance" "show bgp evpn route-type ethernet-segment" \
                "show bgp evpn route-type auto-discovery" "show bgp evpn summary" "show ip bgp summary"; do
                printf '# device:    %s\n# command:   %s\n# collected: %s\n\n' "$h" "$cmd" "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
                cli "$h" "$cmd"
                echo
            done >"$out/$h.txt"
        done
    done
    echo "== details saved to $out"
fi

echo
if [ "$fails" -eq 0 ]; then echo "check_df: both gateways agree in both DCs"; else echo "check_df: $fails DF mismatch(es)"; fi
exit $((fails > 0))
