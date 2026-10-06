#!/usr/bin/env python3
"""Render the dual-DC topology diagrams used in README.md as PNG files.

    python3 tools/gen_png.py          # variant without RT Constraint
    python3 tools/gen_png.py --rtc    # variant with RT Constraint

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
            nodes[h] = box(ax, sx, 37, 14, 5, f"{h}\nspine + EVPN GW · {mgmt(h)}", SPINE_FILL, SPINE_EDGE, fs=9)
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
    fig, ax = canvas(20, 12.5, "Dual DC + DCI – topologia logiczna" + (" (z RT Constraint)" if RTC else ""))
    gws = {}
    for dc, ox in ((1, 1), (2, 58)):
        box(ax, ox, 13, 41, 45.5, fc="none", ec="#999999", ls="--", r=1, z=0,
            title=f"DC{dc} · AS {65000 + 100 * dc} (spine'y), {65001 + 100 * dc}–{65003 + 100 * dc} (pary leafów)")
        gws[dc] = box(ax, ox + 1.5, 43, 38, 12, fc="none", ec=GW_EDGE, ls="--", r=0.8, z=0)
        ax.text(ox + 2, 54.6, f"Domena bram EVPN DC{dc}: all-active (I-ESI 0000:0000:000{dc}:000{dc}:000{dc}), D-path {65000 + 100 * dc}:{dc}",
                fontsize=8.5, color=PURPLE, va="top")
        for i, sx in ((1, ox + 2.5), (2, ox + 21)):
            h = f"marpla-dc-{dc}-s0{i}"
            box(ax, sx, 44, 17, 9, f"{h}\nAS {asn(h)} · Lo0 {lo(h, 'Loopback0')}\nVTEP {lo(h, 'Loopback1')}\nRoute Server EVPN + EVPN GW",
                GW_FILL, GW_EDGE, fs=9)
        for k, (z, (fill, edge, first, vlan, octet, vid)) in enumerate(ZONES.items()):
            zx = ox + 1 + k * 13.4
            h = f"marpla-dc-{dc}-{z}-l0{first}"
            loc = int(f"{str(vlan)[0]}2{dc}")
            txt = (f"dc{dc}-{z} · AS {asn(h)}\nMLAG l0{first}+l0{first + 1}\nVTEP {lo(h, 'Loopback1')}\n"
                   f"VRF {z.upper()} · L3VNI {octet}009000\nRT {vid}:{vid}\n"
                   f"VLAN {vlan} → {octet}000{vlan} (DCI)\nVLAN {loc} → {octet}000{loc} (lokalny)"
                   + (f"\nVLAN 399 → 3000399 (FW HA)" if z == "priv" else "")
                   + f"\nanycast GW 10.{octet}.10.1")
            b = box(ax, zx, 17, 12.6, 16, txt, fill, edge, fs=8.5, align="left", va="top")
            line(ax, [top(b, 0.4), (top(b, 0.4)[0], 43)], BLUE, lw=2)
            line(ax, [top(b, 0.6), (top(b, 0.6)[0], 43)], PURPLE, lw=2, ls=(0, (5, 3)))
            if dc == 1:
                gws.setdefault("zones", []).append(b)
        note = ("RTC (rt-membership): route server wysyła parze leafów\ntylko trasy EVPN jej strefy"
                if RTC else "bez RTC: route server wysyła każdej parze leafów trasy\nwszystkich stref (odrzucane dopiero przy imporcie do VRF)")
        label(ax, ox + 20.5, 38.5, note, fs=8.5, color=GREEN if RTC else RED, bg="#ffffff")
        label(ax, ox + 20.5, 35.2, "RM-UNDERLAY-TO-LEAFS: loopbacki bram drugiego DC nie trafiają do leafów", fs=7.5, bg="#fff2cc")
        fw = box(ax, ox + 13, 14, 15, 2.2, f"marpla-dc-{dc}-fw01 – noga (trunk) w każdej strefie", FW_FILL, FW_EDGE, fs=8,
                 bold_first=False)
    # DCI between gateway domains
    rows = [(BLUE, "-", 2.4, 52.5, "eBGP underlay × 4 (/31)\ntylko Lo0 + VTEP bram (PL-DCI-OUT/IN)"),
            (PURPLE, (0, (5, 3)), 2.4, 48.5, "eBGP EVPN multihop Lo0 ↔ Lo0\nEVPN-OVERLAY-CORE · domain remote"),
            (GREEN, (0, (1, 2)), 3, 44.5, "VXLAN brama ↔ brama, tylko VNI DCI:\n1000110 · 2000210 · 3000310 · 3000399")]
    for color, ls, lw, yy, txt in rows:
        line(ax, [(gws[1][0] + gws[1][2], yy), (gws[2][0], yy)], color, lw=lw, ls=ls)
        label(ax, 50, yy, txt, fs=8, color=color)
    box(ax, 15, 3.5, 70, 6.5,
        "Geo-rozciągnięty klaster FW A/P – węzeł A w DC1, węzeł P w DC2\n"
        "Ten sam anycast gateway (IP + MAC 00:1c:73:00:dc:99) w obu DC · HA po VLAN 399 (czyste L2 przez DCI)\n"
        "Ruch między strefami tylko przez FW (router-on-a-stick) – strefy to osobne VRF-y bez przecieków",
        FW_FILL, FW_EDGE, fs=9, ls="--")
    legend(ax, 87, 9.5, [(BLUE, "-", 2, "eBGP underlay"), (PURPLE, (0, (5, 3)), 2, "eBGP EVPN"),
                         (GREEN, (0, (1, 2)), 3, "VXLAN")], fs=8.5)
    fig.savefig(os.path.join(OUT, "topology-logical.png"), dpi=110, bbox_inches="tight")


# --------------------------------------------------------------------------- control plane
def control_plane():
    fig, ax = canvas(16, 9, "Płaszczyzna sterowania EVPN w DC1 – " + ("z RT Constraint" if RTC else "bez RT Constraint"))
    rs = box(ax, 25, 41, 50, 9, "Route servery EVPN + bramy: marpla-dc-1-s01, marpla-dc-1-s02\n"
             "importują wszystkie strefy (EXT, WEW, PRIV) – obsługują DCI dla każdej z nich"
             + ("\nrt-membership: default-route-target only" if RTC else ""), GW_FILL, GW_EDGE, fs=10)
    rts = {"wew": "RT 20:20 · 210:210 · 221:221", "priv": "RT 30:30 · 310:310 · 321:321 · 399:399",
           "ext": "RT 10:10 · 110:110 · 121:121"}
    pairs = {}
    for k, (z, (fill, edge, first, *_)) in enumerate(ZONES.items()):
        pairs[z] = box(ax, 4 + k * 32.5, 6, 27, 11, f"dc1-{z}-l0{first} + l0{first + 1}\nVRF {z.upper()}\nimportuje: {rts[z]}",
                       fill, edge, fs=9.5)
    for k, (z, b) in enumerate(pairs.items()):
        for j, (rz, (fill, edge, *_)) in enumerate(ZONES.items()):
            own = rz == z
            if RTC and not own:
                continue
            x0 = rs[0] + rs[2] * (0.2 + 0.3 * k) + (j - 1) * 1.6
            x1 = b[0] + b[2] * (0.3 + 0.2 * j)
            line(ax, [(x0, rs[1]), (x1, b[1] + b[3])], edge, lw=3 if own else 1.6, ls="-" if own else (0, (3, 2)),
                 arrow=True, z=2 if own else 1)
        if RTC:
            line(ax, [top(b, 0.85), (rs[0] + rs[2] * (0.27 + 0.3 * k), rs[1])], "#333333", lw=1.2, ls=(0, (1, 2)), arrow=True)
            label(ax, b[0] + b[2] * 0.5, 23.5, f"rt-membership: {rts[z][3:]}", fs=8, color="#333333")
            label(ax, b[0] + b[2] * 0.5, 30, f"trasy {z} ✓", fs=9, color=ZONES[z][1], bold=True)
        else:
            label(ax, b[0] + b[2] * 0.5, 28,
                  f"trasy {z}: import do VRF ✓\ntrasy pozostałych stref: w tablicy BGP,\nodrzucane dopiero przy imporcie",
                  fs=8, color="#333333")
    msg = ("Zmierzone na dc1-priv-l03: 40 ścieżek EVPN w tablicy BGP, każda z RT strefy priv\n"
           "(bez RTC: 144 ścieżki, z czego 104 wyłącznie z RT innych stref)") if RTC else \
          ("Zmierzone na dc1-priv-l03: 144 ścieżki EVPN w tablicy BGP, 104 z nich wyłącznie z RT stref ext/wew\n"
           "– separacja stref tylko na poziomie VRF/importu, nie płaszczyzny sterowania")
    label(ax, 50, 2.5, msg, fs=9.5, color=GREEN if RTC else RED, bg="#ffffff")
    fig.savefig(os.path.join(OUT, "control-plane.png"), dpi=110, bbox_inches="tight")


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    physical()
    logical()
    control_plane()
    print("written to", OUT, "(RTC variant)" if RTC else "(no RTC variant)")
