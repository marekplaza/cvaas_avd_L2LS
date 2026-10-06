#!/usr/bin/env python3
"""Render the dual-DC topology diagrams used in README.md as PNG files.

    python3 tools/gen_png.py          # multi-domain: per-zone gateways on the leaf pairs, RTC

Writes docs/topology-physical.png, docs/topology-logical.png and
docs/control-plane.png. Addresses and ASNs come from the AVD structured
configs, so run it after `make build`. Requires matplotlib and PyYAML.
"""
from __future__ import annotations

import glob
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import yaml  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SC_DIR = os.path.join(ROOT, "avd", "intended", "structured_configs")
OUT = os.path.join(ROOT, "docs")
RTC = "--rtc" in sys.argv

plt.rcParams["font.family"] = "DejaVu Sans"

ZONES = {  # zone: (fill, edge, first leaf, stretched VLAN, octet, vrf_id)
    "wew": ("#dae8fc", "#6c8ebf", 1, 210, 2, 20),
    "priv": ("#d5e8d4", "#82b366", 3, 310, 3, 30),
    "ext": ("#ffe6cc", "#d79b00", 5, 110, 1, 10),
}
GW_FILL, GW_EDGE = "#e1d5e7", "#9673a6"
SPINE_FILL, SPINE_EDGE = "#f5f5f5", "#666666"
FW_FILL, FW_EDGE = "#f8cecc", "#b85450"
BLUE, PURPLE, GREEN, RED, GOLD, GREY = "#0050ef", "#9673a6", "#2d7600", "#b85450", "#d6b656", "#666666"


def load() -> dict:
    return {os.path.basename(f)[:-4]: yaml.safe_load(open(f, encoding="utf-8")) for f in sorted(glob.glob(SC_DIR + "/*.yml"))}


SC = load()


def lo(host: str, name: str) -> str:
    return next(l["ip_address"].split("/")[0] for l in SC[host]["loopback_interfaces"] if l["name"] == name)


def asn(host: str) -> str:
    return SC[host]["router_bgp"]["as"]


def mgmt(host: str) -> str:
    return SC[host]["management_interfaces"][0]["ip_address"].split("/")[0]


def canvas(w: float, h: float, title: str):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100 * h / w)
    ax.axis("off")
    ax.text(1, 100 * h / w - 1.5, title, fontsize=17, fontweight="bold", va="top")
    return fig, ax


def box(ax, x, y, w, h, text="", fc="#ffffff", ec="#333333", fs=9, lw=1.2, ls="-", align="center",
        va="center", bold_first=True, r=0.6, z=2, title=None):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}", fc=fc, ec=ec, lw=lw,
                                ls=ls, zorder=z))
    if title:
        ax.text(x + 0.6, y + h - 0.5, title, fontsize=fs + 1, fontweight="bold", va="top", ha="left", zorder=z + 1)
    if text:
        lines = text.split("\n")
        tx = x + w / 2 if align == "center" else x + 0.6
        lh = fs * 1.32  # line height in points
        if va == "center":
            anchor_y, first_off = y + h / 2, (len(lines) - 1) * lh / 2
        else:
            anchor_y, first_off = y + h - 0.5, -lh / 2
        for i, ln in enumerate(lines):
            ax.annotate(ln, (tx, anchor_y), xytext=(0, first_off - i * lh), textcoords="offset points",
                        fontsize=fs if i == 0 else fs - 0.5, ha=align, va="center", zorder=z + 1,
                        fontweight="bold" if (i == 0 and bold_first) else "normal")
    return (x, y, w, h)


def line(ax, pts, color, lw=1.2, ls="-", z=1, arrow=False):
    xs, ys = zip(*pts)
    ax.plot(xs, ys, color=color, lw=lw, ls=ls, zorder=z, solid_capstyle="round")
    if arrow:
        ax.annotate("", xy=pts[-1], xytext=pts[-2], arrowprops=dict(arrowstyle="-|>", color=color, lw=lw), zorder=z)


def label(ax, x, y, text, fs=8, color="#000000", bg="#ffffff", ha="center", z=5, bold=False):
    ax.text(x, y, text, fontsize=fs, color=color, ha=ha, va="center", zorder=z, fontweight="bold" if bold else "normal",
            bbox=dict(boxstyle="round,pad=0.25", fc=bg, ec="none") if bg else None, linespacing=1.25)


def top(b, f=0.5):
    return (b[0] + b[2] * f, b[1] + b[3])


def bottom(b, f=0.5):
    return (b[0] + b[2] * f, b[1])


def legend(ax, x, y, rows, fs=9):
    for i, (color, ls, lw, text) in enumerate(rows):
        yy = y - i * 2.1
        line(ax, [(x, yy), (x + 4, yy)], color, lw=lw, ls=ls, z=3)
        ax.text(x + 5, yy, text, fontsize=fs, va="center")


# --------------------------------------------------------------------------- physical
def physical():
    fig, ax = canvas(20, 12, "Dual DC + DCI – topologia fizyczna (containerlab, 18 × cEOS 4.35.6M)")
    nodes = {}
    for dc, ox in ((1, 1), (2, 51)):
        box(ax, ox, 7, 48, 41, fc="none", ec="#999999", ls="--", r=1, z=0,
            title=f"DC{dc} · marpla-DC{dc} · AS {65000 + 100 * dc}–{65003 + 100 * dc}")
        for i, sx in ((1, ox + 6), (2, ox + 28)):
            h = f"marpla-dc-{dc}-s0{i}"
            nodes[h] = box(ax, sx, 37, 14, 5, f"{h}\nspine / route server · {mgmt(h)}", SPINE_FILL, SPINE_EDGE, fs=9)
        for k, (z, (fill, edge, first, *_)) in enumerate(ZONES.items()):
            zx = ox + 1 + k * 15.7
            box(ax, zx, 17, 15, 12, fc=fill, ec=edge, r=0.8, z=0, title=f"dmz:{z} · AS {asn(f'marpla-dc-{dc}-{z}-l0{first}')}", fs=9)
            for j in (0, 1):
                n = first + j
                h = f"marpla-dc-{dc}-{z}-l0{n}"
                nodes[h] = box(ax, zx + 0.5 + j * 7.3, 18.5, 6.7, 6, f"{z}-l0{n}\n{mgmt(h)}", "#ffffff", edge, fs=8.5)
            a, b = nodes[f"marpla-dc-{dc}-{z}-l0{first}"], nodes[f"marpla-dc-{dc}-{z}-l0{first + 1}"]
            for yy in (0.38, 0.62):
                line(ax, [(a[0] + a[2], a[1] + a[3] * yy), (b[0], b[1] + b[3] * yy)], GOLD, lw=2.2, z=3)
            label(ax, (a[0] + a[2] + b[0]) / 2, a[1] - 0.9, "MLAG Et3+Et4", fs=7, bg=None)
        fw = f"marpla-dc-{dc}-fw01"
        nodes[fw] = box(ax, ox + 17, 9, 14, 4.5, f"{fw}\nwęzeł klastra FW ({'A' if dc == 1 else 'P'})", FW_FILL, FW_EDGE, fs=9)
        leafs = [f"marpla-dc-{dc}-{z}-l0{ZONES[z][2] + j}" for z in ZONES for j in (0, 1)]
        for idx, l in enumerate(leafs, 1):
            line(ax, [top(nodes[l], 0.3), bottom(nodes[f"marpla-dc-{dc}-s01"], idx / 7)], GREY, lw=1)
            line(ax, [top(nodes[l], 0.7), bottom(nodes[f"marpla-dc-{dc}-s02"], idx / 7)], GREY, lw=1)
            line(ax, [top(nodes[fw], idx / 7), bottom(nodes[l])], RED, lw=1)
    # DCI: 4 links routed above the spines
    links = [("marpla-dc-1-s01", 0.3, "marpla-dc-2-s01", 0.3, "dc1-s01 Et7 10.100.0.0/31 ⇄ dc2-s01 Et7 .1"),
             ("marpla-dc-1-s01", 0.7, "marpla-dc-2-s02", 0.3, "dc1-s01 Et8 10.100.0.2/31 ⇄ dc2-s02 Et8 .3"),
             ("marpla-dc-1-s02", 0.3, "marpla-dc-2-s01", 0.7, "dc1-s02 Et8 10.100.0.6/31 ⇄ dc2-s01 Et8 .7"),
             ("marpla-dc-1-s02", 0.7, "marpla-dc-2-s02", 0.7, "dc1-s02 Et7 10.100.0.4/31 ⇄ dc2-s02 Et7 .5")]
    for k, (a, fa, b, fb, txt) in enumerate(links):
        yy = 55.4 - k * 1.8
        pa, pb = top(nodes[a], fa), top(nodes[b], fb)
        line(ax, [pa, (pa[0], yy), (pb[0], yy), pb], RED, lw=2.6, z=2)
        label(ax, 50, yy, txt, fs=8)
    legend(ax, 2, 4.5, [(GREY, "-", 1, "uplink leaf → spine (Et1 → s01, Et2 → s02; port spine'a = numer leafa)"),
                        (GOLD, "-", 2.2, "MLAG peer-link (Et3 + Et4)")])
    legend(ax, 52, 4.5, [(RED, "-", 1, "leaf Et5 → FW (LACP, Port-Channel5 na parze MLAG)"),
                         (RED, "-", 2.6, "łącze DCI: 4 × /31 spine ↔ spine (pełna siatka 2 × 2), MTU 9214")])
    fig.savefig(os.path.join(OUT, "topology-physical.png"), dpi=110, bbox_inches="tight")


# --------------------------------------------------------------------------- logical
def logical():
    fig, ax = canvas(20, 13.5, "Dual DC + DCI – topologia logiczna, multi-domain (każda strefa = osobna domena EVPN)")
    zb = {}
    for dc, ox in ((1, 1), (2, 58)):
        o = 3 - dc
        box(ax, ox, 21, 41, 42.5, fc="none", ec="#999999", ls="--", r=1, z=0,
            title=f"DC{dc} · AS {65000 + 100 * dc} (spine'y), {65001 + 100 * dc}–{65003 + 100 * dc} (pary leafów)")
        sp = []
        for i, sx in ((1, ox + 3), (2, ox + 22)):
            h = f"marpla-dc-{dc}-s0{i}"
            sp.append(box(ax, sx, 51, 16, 7, f"{h}\nAS {asn(h)} · Lo0 {lo(h, 'Loopback0')}\nroute server EVPN (bez VTEP/VRF)\n+ tranzyt underlay DCI",
                          SPINE_FILL, SPINE_EDGE, fs=8.5))
        for k, (z, (fill, edge, first, vlan, octet, vid)) in enumerate(ZONES.items()):
            zx = ox + 1 + k * 13.4
            h = f"marpla-dc-{dc}-{z}-l0{first}"
            loc = int(f"{str(vlan)[0]}2{dc}")
            txt = (f"dc{dc}-{z} · AS {asn(h)}\nMLAG l0{first}+l0{first + 1} · VTEP {lo(h, 'Loopback1')}\n"
                   f"EVPN GW strefy (domain remote)\n⇄ dc{o}-{z} {'10.10' + str(o)}.1.{first}/.{first + 1}\n"
                   f"VRF {z.upper()} · L3VNI {octet}009000 · RT {vid}:{vid}\n"
                   f"VLAN {vlan} → {octet}000{vlan} (DCI)\nVLAN {loc} → {octet}000{loc} (lokalny)"
                   + (f"\nVLAN 399 → 3000399 (FW HA)" if z == "priv" else ""))
            b = box(ax, zx, 27, 12.6, 15.5, txt, fill, edge, fs=7.8, align="left", va="top")
            zb[(dc, z)] = b
            for s_ in sp:
                line(ax, [top(b, 0.35), bottom(s_, 0.3 + 0.2 * k)], BLUE, lw=1.4)
                line(ax, [top(b, 0.65), bottom(s_, 0.4 + 0.2 * k)], PURPLE, lw=1.4, ls=(0, (5, 3)))
        label(ax, ox + 20.5, 47.5, "RTC + RM-RTC-LOCAL-ONLY: para ogłasza tylko RT swojej strefy\n– route server wysyła jej tylko trasy jej strefy",
              fs=8, color=GREEN, bg="#fff2cc")
        box(ax, ox + 13, 22, 15, 2.6, f"marpla-dc-{dc}-fw01 – noga w każdej strefie", FW_FILL, FW_EDGE, fs=8, bold_first=False)
    # DCI underlay between the spine layers
    line(ax, [(42, 54.5), (58, 54.5)], BLUE, lw=2.4)
    label(ax, 50, 54.5, "eBGP underlay × 4 (/31)\ntylko Lo0 + VTEP leafów", fs=8, color=BLUE)
    # per-zone DCI sessions, routed below the zone boxes
    for k, z in enumerate(ZONES):
        a, b = zb[(1, z)], zb[(2, z)]
        ye, yv = 19 - k * 2.6, 17.9 - k * 2.6
        pa, pb = bottom(a, 0.35), bottom(b, 0.35)
        line(ax, [pa, (pa[0], ye), (pb[0], ye), pb], PURPLE, lw=2, ls=(0, (5, 3)))
        pa, pb = bottom(a, 0.65), bottom(b, 0.65)
        line(ax, [pa, (pa[0], yv), (pb[0], yv), pb], GREEN, lw=2.6, ls=(0, (1, 2)))
        first = ZONES[z][2]
        label(ax, 50, ye, f"{z}: EVPN multihop l0{first}/l0{first + 1} ⇄ l0{first}/l0{first + 1} (domain remote)", fs=7.5, color=PURPLE)
        label(ax, 50, yv, f"{z}: VXLAN 10.101.2.{first} ⇄ 10.102.2.{first}", fs=7.5, color=GREEN)
    box(ax, 15, 3, 70, 6,
        "Geo-rozciągnięty klaster FW A/P – węzeł A w DC1, węzeł P w DC2\n"
        "Ten sam anycast gateway (IP + MAC 00:1c:73:00:dc:99) w obu DC · HA po VLAN 399 (L2 przez DCI w domenie priv)\n"
        "Ruch między strefami tylko przez FW – strefy to osobne VRF-y i osobne domeny EVPN",
        FW_FILL, FW_EDGE, fs=9, ls="--")
    legend(ax, 87, 8.5, [(BLUE, "-", 2, "eBGP underlay"), (PURPLE, (0, (5, 3)), 2, "eBGP EVPN"),
                         (GREEN, (0, (1, 2)), 3, "VXLAN")], fs=8.5)
    fig.savefig(os.path.join(OUT, "topology-logical.png"), dpi=110, bbox_inches="tight")


# --------------------------------------------------------------------------- control plane
def control_plane():
    fig, ax = canvas(18, 10, "Płaszczyzna sterowania EVPN – multi-domain: każda strefa osobno, także przez DCI")
    rts = {"wew": "20:20 · 210:210 · 22x:22x", "priv": "30:30 · 310:310 · 32x:32x · 399:399", "ext": "10:10 · 110:110 · 12x:12x"}
    for dc, ox in ((1, 2), (2, 54)):
        rs = box(ax, ox + 6, 43, 32, 7, f"Route servery DC{dc}: marpla-dc-{dc}-s01/s02\nbez VTEP i VRF · tylko trasy stref DC{dc}\n"
                 "rt-membership: default-route-target only", SPINE_FILL, SPINE_EDGE, fs=9)
        for k, (z, (fill, edge, first, *_)) in enumerate(ZONES.items()):
            b = box(ax, ox + k * 15, 14, 13.5, 10, f"dc{dc}-{z} l0{first}+l0{first + 1}\nEVPN GW strefy\nRT {rts[z]}",
                    fill, edge, fs=7.8)
            x0 = rs[0] + rs[2] * (0.2 + 0.3 * k)
            line(ax, [(x0 - 0.8, rs[1]), (b[0] + b[2] * 0.4, b[1] + b[3])], edge, lw=2.6, arrow=True, z=2)
            line(ax, [(b[0] + b[2] * 0.6, b[1] + b[3]), (x0 + 0.8, rs[1])], "#333333", lw=1, ls=(0, (1, 2)), arrow=True)
            label(ax, b[0] + b[2] * 0.5, 33, f"tylko {z}", fs=8.5, color=edge, bold=True)
            pairs = ax._marpla_pairs = getattr(ax, "_marpla_pairs", {})
            pairs[(dc, z)] = b
    for k, z in enumerate(ZONES):
        a, b = ax._marpla_pairs[(1, z)], ax._marpla_pairs[(2, z)]
        yy = 11.5 - k * 2.4
        pa, pb = bottom(a), bottom(b)
        line(ax, [pa, (pa[0], yy), (pb[0], yy), pb], ZONES[z][1], lw=2.4, ls=(0, (5, 3)))
        label(ax, 50, yy + 0.8, f"{z}: EVPN-OVERLAY-CORE tylko między parami {z} (RT {z}, domain remote)", fs=8, color=ZONES[z][1], bg=None)
    label(ax, 50, 39, "RM-RTC-LOCAL-ONLY: brama ogłasza tylko członkostwo RT, które sama generuje –\n"
                      "członkostwo 0/0 route serverów jednego DC nie przechodzi przez DCI do drugiego", fs=8.5, color="#333333", bg="#fff2cc")
    label(ax, 50, 2, "Zmierzone: tablica BGP EVPN leafa zawiera tylko trasy jego strefy (dc1-priv-l03: 46 ścieżek, wszystkie priv; "
                     "dc1-wew-l01: 37, wszystkie wew)\nroute servery: tylko trasy stref własnego DC (dc1-s01: 52 ścieżki), "
                     "trasy z drugiego DC kończą się na bramie strefy", fs=8.5, color=GREEN)
    fig.savefig(os.path.join(OUT, "control-plane.png"), dpi=110, bbox_inches="tight")


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    physical()
    logical()
    control_plane()
    print("written to", OUT, "(multi-domain)")
