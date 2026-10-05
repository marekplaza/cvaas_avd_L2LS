#!/usr/bin/env python3
"""Generate the ANTA catalog with the dual-DC BGP / EVPN / DCI tests.

Expected values (peers, loopbacks, VTEPs, VNIs) are taken from the AVD
structured configs, so run it after `make build`. Every test is limited to one
device with an ANTA tag equal to the hostname.

What is verified:
  gateways (spines)
    - all BGP sessions up: leaf underlay, leaf EVPN, DCI underlay, EVPN core
    - BGP peer count per address family
    - DCI peers use the DCI route-maps, leaf peers get RM-UNDERLAY-TO-LEAFS
    - DCI underlay exchanges exactly the gateway loopbacks (Lo0 + VTEP)
    - VTEP peers = local leaf pairs + remote gateways
    - only DCI VNIs are configured on the gateway
    - EVPN type-5 routes for the DC-local subnets of both DCs
  leafs
    - all BGP sessions up and peer counts
    - VTEP peers = only the local gateways (no tunnels to the other DC)
    - zone VNIs only
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

    # Interface IP -> gateway hostname: resolves which gateway sits behind a DCI peer address
    owner_of_ip = {}
    for h, c in spines.items():
        for e in c.get("ethernet_interfaces", []):
            if e.get("ip_address"):
                owner_of_ip[e["ip_address"].split("/")[0]] = h

    vtep_ip = {h: loopback(c, "Loopback1") for h, c in devices.items()}
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
                {"afi": "ipv4", "safi": "unicast", "vrf": "default", "num_peers": len(ipv4)},
            ]})
        add("anta.tests.vxlan", "VerifyVxlanVniBinding", h, {"bindings": bindings(c)})

    for h, c in spines.items():
        dc = dc_of(h)
        dci = [n for n in neighbors(c) if n.get("description", "").startswith("DCI_")]
        leaf_peers = [n for n in neighbors(c) if n.get("peer_group") == "IPv4-UNDERLAY-PEERS"]
        add("anta.tests.routing.bgp", "VerifyBgpRouteMaps", h, {"bgp_peers": [
            *({"peer_address": n["ip_address"], "vrf": "default",
               "inbound_route_map": n["route_map_in"], "outbound_route_map": n["route_map_out"]} for n in dci),
            *({"peer_address": n["ip_address"], "vrf": "default",
               "outbound_route_map": "RM-UNDERLAY-TO-LEAFS"} for n in leaf_peers),
        ]})
        own = [loopback(c, "Loopback0") + "/32", vtep_ip[h] + "/32"]
        add("anta.tests.routing.bgp", "VerifyBGPExchangedRoutes", h, {"bgp_peers": [
            {"peer_address": n["ip_address"], "vrf": "default",
             "advertised_routes": own,
             "received_routes": [loopback(spines[owner_of_ip[n["ip_address"]]], "Loopback0") + "/32",
                                 vtep_ip[owner_of_ip[n["ip_address"]]] + "/32"]}
            for n in dci]})
        local_leaf_vteps = {vtep_ip[l] for l in leafs if dc_of(l) == dc}
        remote_gws = {vtep_ip[s] for s in spines if dc_of(s) != dc}
        add("anta.tests.vxlan", "VerifyVxlanVtep", h, {"vteps": sorted(local_leaf_vteps | remote_gws)})
        add("anta.tests.evpn", "VerifyEVPNType5Routes", h, {"prefixes": [
            {"address": f"10.{octet}.2{d}.0/24", "vni": vrf_vni(c, zone.upper())}
            for zone, (_, octet) in ZONES.items() for d in (1, 2)]})
        add("anta.tests.routing.bgp", "VerifyEVPNType2Route", h, {"vxlan_endpoints": [
            {"address": f"10.{octet}.10.{FW_HOST_OCTET[d]}", "vni": c_vni}
            for zone, (vlan, octet) in ZONES.items()
            for c_vni in [next(v["vni"] for v in vxlan(c)["vlans"] if v["id"] == vlan)]
            for d in (1, 2)]})

    for h, c in leafs.items():
        dc, zone = dc_of(h), zone_of(h)
        vlan, octet = ZONES[zone]
        local_gws = {vtep_ip[s] for s in spines if dc_of(s) == dc}
        add("anta.tests.vxlan", "VerifyVxlanVtep", h, {"vteps": sorted(local_gws)})
        add("anta.tests.evpn", "VerifyEVPNType5Routes", h, {"prefixes": [
            {"address": f"10.{octet}.2{3 - dc}.0/24", "vni": vrf_vni(c, zone.upper())}]})
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
