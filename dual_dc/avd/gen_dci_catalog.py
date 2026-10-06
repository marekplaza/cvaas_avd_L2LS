#!/usr/bin/env python3
"""Generate the ANTA catalog with the dual-DC multi-domain BGP / EVPN / DCI tests.

Expected values (peers, loopbacks, VTEPs, VNIs) are taken from the AVD
structured configs, so run it after `make build`. Every test is limited to one
device with an ANTA tag equal to the hostname.

Multi-domain (variant A): every zone's MLAG leaf pair is the EVPN gateway of
that zone; spines are EVPN route servers and DCI underlay transit only.

What is verified:
  all devices
    - all BGP sessions up; peer count for EVPN, rt-membership (RTC) and IPv4
  spines (route servers + DCI transit)
    - DCI peers use the DCI route-maps
    - DCI underlay exchanges the leaf loopbacks (Lo0 + VTEP) of both DCs
  leafs (zone gateways)
    - EVPN-OVERLAY-CORE peers are exactly the same zone's leaf pair in the other DC
      (part of the session/peer-count tests: 2 route servers + 2 remote zone peers)
    - VTEP peers = only the same zone's leaf pair in the other DC
    - zone VNIs only
    - RT Constraint: the BGP EVPN table holds only routes with an RT of the leaf's zone
      (custom test marpla_tests.VerifyEVPNRoutesMatchImportedRT)
    - EVPN type-5 route for the same zone's subnet that is local to the other DC
  traffic (needs `make fw_test` first so the firewalls' ARP/MAC are learned)
    - EVPN type-2 route of the remote firewall node on the stretched VLAN
"""
from __future__ import annotations

import glob
import os
from collections import defaultdict

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
STRUCTURED = os.path.join(HERE, "intended", "structured_configs")
OUTPUT = os.path.join(HERE, "anta_catalogs", "dci_tests.yml")

# zone -> (stretched VLAN, second octet of the zone subnets)
ZONES = {"ext": (110, 1), "wew": (210, 2), "priv": (310, 3)}
FW_HOST_OCTET = {1: 11, 2: 12}  # FW node address in each DC


def load() -> dict[str, dict]:
    devices = {}
    for path in sorted(glob.glob(os.path.join(STRUCTURED, "*.yml"))):
        with open(path, encoding="utf-8") as f:
            devices[os.path.basename(path)[:-4]] = yaml.safe_load(f)
    return devices


def loopback(cfg: dict, name: str) -> str:
    for lo in cfg.get("loopback_interfaces", []):
        if lo["name"] == name:
            return lo["ip_address"].split("/")[0]
    raise KeyError(name)


def dc_of(hostname: str) -> int:
    return int(hostname.split("-")[2])


def zone_of(hostname: str) -> str | None:
    part = hostname.split("-")[3]
    return part if part in ZONES else None


def neighbors(cfg: dict) -> list[dict]:
    return cfg.get("router_bgp", {}).get("neighbors", [])


def vxlan(cfg: dict) -> dict:
    return cfg.get("vxlan_interface", {}).get("vxlan1", {}).get("vxlan", {})


def bindings(cfg: dict) -> dict:
    vx = vxlan(cfg)
    result = {v["vni"]: v["id"] for v in vx.get("vlans", [])}
    result.update({v["vni"]: v["name"] for v in vx.get("vrfs", [])})
    return dict(sorted(result.items()))


def vrf_vni(cfg: dict, vrf: str) -> int:
    return next(v["vni"] for v in vxlan(cfg)["vrfs"] if v["name"] == vrf)


def main() -> None:
    devices = load()
    spines = {h: c for h, c in devices.items() if h.split("-")[3].startswith("s")}  # marpla-dc-<n>-sNN
    leafs = {h: c for h, c in devices.items() if h not in spines}
    tests: dict[str, list] = defaultdict(list)

    def add(module: str, test: str, host: str, inputs: dict) -> None:
        tests[module].append({test: {**inputs, "filters": {"tags": [host]}}})

    for h, c in devices.items():
        nbrs = neighbors(c)
        # TCP queues are only a snapshot: right after a deploy under high lab load they are often
        # briefly non-empty, which says nothing about session health.
        add("anta.tests.routing.bgp", "VerifyBGPPeerSession", h,
            {"check_tcp_queues": False,
             "bgp_peers": [{"peer_address": n["ip_address"], "vrf": "default"} for n in nbrs]})
        evpn = [n for n in nbrs if n.get("peer_group", "").startswith("EVPN-OVERLAY")]
        ipv4 = [n for n in nbrs if n not in evpn]
        add("anta.tests.routing.bgp", "VerifyBGPPeerCount", h,
            {"address_families": [
                {"afi": "evpn", "num_peers": len(evpn)},
                {"afi": "rt-membership", "num_peers": len(evpn)},
                {"afi": "ipv4", "safi": "unicast", "vrf": "default", "num_peers": len(ipv4)},
            ]})

    for h, c in spines.items():
        dc = dc_of(h)
        dci = [n for n in neighbors(c) if n.get("description", "").startswith("DCI_")]
        add("anta.tests.routing.bgp", "VerifyBgpRouteMaps", h, {"bgp_peers": [
            {"peer_address": n["ip_address"], "vrf": "default",
             "inbound_route_map": n["route_map_in"], "outbound_route_map": n["route_map_out"]} for n in dci]})
        local = sorted({f"{loopback(c2, n)}/32" for l, c2 in leafs.items() if dc_of(l) == dc for n in ("Loopback0", "Loopback1")})
        remote = sorted({f"{loopback(c2, n)}/32" for l, c2 in leafs.items() if dc_of(l) != dc for n in ("Loopback0", "Loopback1")})
        # check_active: False - each loopback arrives over both DCI links (ECMP); only one path is "best"
        add("anta.tests.routing.bgp", "VerifyBGPExchangedRoutes", h, {"check_active": False, "bgp_peers": [
            {"peer_address": n["ip_address"], "vrf": "default", "advertised_routes": local, "received_routes": remote}
            for n in dci]})

    vtep_ip = {h: loopback(c, "Loopback1") for h, c in leafs.items()}
    for h, c in leafs.items():
        dc, zone = dc_of(h), zone_of(h)
        vlan, octet = ZONES[zone]
        remote_pair = {vtep_ip[l] for l in leafs if dc_of(l) != dc and zone_of(l) == zone}
        add("anta.tests.vxlan", "VerifyVxlanVtep", h, {"vteps": sorted(remote_pair)})
        add("anta.tests.vxlan", "VerifyVxlanVniBinding", h, {"bindings": bindings(c)})
        add("anta.tests.evpn", "VerifyEVPNType5Routes", h, {"prefixes": [
            {"address": f"10.{octet}.2{3 - dc}.0/24", "vni": vrf_vni(c, zone.upper())}]})
        bgp = c["router_bgp"]
        imported = {rt for v in bgp.get("vlans", []) for rt in v["route_targets"]["both"]}
        imported |= {rt for v in bgp.get("vrfs", []) for imp in v["route_targets"]["import"] for rt in imp["route_targets"]}
        add("marpla_tests", "VerifyEVPNRoutesMatchImportedRT", h, {"route_targets": sorted(imported)})
        l2vni = next(v["vni"] for v in vxlan(c)["vlans"] if v["id"] == vlan)
        add("anta.tests.routing.bgp", "VerifyEVPNType2Route", h, {"vxlan_endpoints": [
            {"address": f"10.{octet}.10.{FW_HOST_OCTET[3 - dc]}", "vni": l2vni}]})

    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write("---\n# Generated by gen_dci_catalog.py from intended/structured_configs - do not edit.\n")
        yaml.safe_dump(dict(tests), f, sort_keys=False, default_flow_style=False)
    print(f"Wrote {OUTPUT}: {sum(len(v) for v in tests.values())} tests for {len(devices)} devices")


if __name__ == "__main__":
    main()
