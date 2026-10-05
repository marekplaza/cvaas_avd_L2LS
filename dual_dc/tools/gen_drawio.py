"""Generate dual_dc/topology.drawio from the AVD structured configs.

Pages: Fizyczna, Logiczna, Routing i P2P DC1, Routing i P2P DC2.
Run after `make build`:  python3 tools/gen_drawio.py
Set DRAWIO_PREVIEW=1 (needs Pillow) to also write rough PNG previews next to this script.
"""
import html
import os
import sys
try:
    from PIL import Image, ImageDraw
except ImportError:
    Image = None

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "topology.drawio")
PREV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "preview_{}.png")

ZONE = {  # fill, stroke
    "wew": ("#dae8fc", "#6c8ebf"),
    "priv": ("#d5e8d4", "#82b366"),
    "ext": ("#ffe6cc", "#d79b00"),
}
SPINE = "fillColor=#f5f5f5;strokeColor=#666666;"
GW = "fillColor=#e1d5e7;strokeColor=#9673a6;"
FW = "fillColor=#f8cecc;strokeColor=#b85450;"
DCBOX = "fillColor=none;strokeColor=#999999;dashed=1;verticalAlign=top;align=left;spacingLeft=10;spacingTop=4;fontStyle=1;fontSize=16;rounded=1;arcSize=2;"
BASE = "rounded=1;whiteSpace=wrap;html=1;arcSize=8;fontSize=11;"
TEXT = "text;html=1;align=left;verticalAlign=top;whiteSpace=wrap;fontSize=11;"

E_PHY = "endArrow=none;html=1;strokeWidth=1.5;strokeColor=#333333;"
E_DCI = "endArrow=none;html=1;strokeWidth=3;strokeColor=#b85450;"
E_UND = "endArrow=none;html=1;strokeWidth=2;strokeColor=#0050ef;"
E_EVPN = "endArrow=none;html=1;strokeWidth=2;strokeColor=#9673a6;dashed=1;dashPattern=8 4;"
E_VX = "endArrow=classic;startArrow=classic;html=1;strokeWidth=3;strokeColor=#2d7600;dashed=1;dashPattern=1 3;"
E_FW = "endArrow=none;html=1;strokeWidth=1.5;strokeColor=#b85450;"
E_MLAG = "endArrow=none;html=1;strokeWidth=2;strokeColor=#d6b656;"


class Page:
    def __init__(self, name, w, h):
        self.name, self.w, self.h = name, w, h
        self.cells, self.geo, self.n = [], {}, 0

    def _id(self):
        self.n += 1
        return f"{self.name.replace(' ', '')}-{self.n}"

    def box(self, label, x, y, w, h, style, cid=None):
        cid = cid or self._id()
        self.geo[cid] = (x, y, w, h, style, label)
        self.cells.append(
            f'<mxCell id="{cid}" value="{html.escape(label)}" style="{style}" vertex="1" parent="1">'
            f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')
        return cid

    def edge(self, src, tgt, style, label="", sx=None, sy=None, tx=None, ty=None, points=None, lpos=0):
        cid = self._id()
        pts = ""
        if points:
            pts = '<Array as="points">' + "".join(f'<mxPoint x="{x}" y="{y}"/>' for x, y in points) + "</Array>"
        if sx is not None:
            style += f"exitX={sx};exitY={sy};exitDx=0;exitDy=0;"
        if tx is not None:
            style += f"entryX={tx};entryY={ty};entryDx=0;entryDy=0;"
        self.geo[cid] = ("edge", src, tgt, style, label, (sx, sy, tx, ty), points or [], lpos)
        lbl = f' value="{html.escape(label)}"' if label else ' value=""'
        self.cells.append(
            f'<mxCell id="{cid}"{lbl} style="{style}labelBackgroundColor=#ffffff;fontSize=10;" edge="1" parent="1" source="{src}" target="{tgt}">'
            f'<mxGeometry x="{lpos}" relative="1" as="geometry">{pts}</mxGeometry></mxCell>')
        return cid

    def xml(self):
        body = "".join(self.cells)
        return (f'<diagram id="{self.name}" name="{self.name}"><mxGraphModel dx="1600" dy="900" grid="1" gridSize="10" '
                f'guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" '
                f'pageWidth="{self.w}" pageHeight="{self.h}" math="0" shadow="0"><root><mxCell id="0"/>'
                f'<mxCell id="1" parent="0"/>{body}</root></mxGraphModel></diagram>')

    def preview(self, path):
        img = Image.new("RGB", (self.w, self.h), "white")
        d = ImageDraw.Draw(img)

        def col(style, key, default):
            for part in style.split(";"):
                if part.startswith(key + "="):
                    v = part.split("=", 1)[1]
                    return None if v == "none" else v
            return default

        def anchor(cid, fx, fy):
            x, y, w, h, *_ = self.geo[cid]
            if fx is None:
                return x + w / 2, y + h / 2
            return x + w * fx, y + h * fy

        for cid, g in self.geo.items():
            if g[0] != "edge":
                x, y, w, h, style, label = g
                fill = col(style, "fillColor", None)
                stroke = col(style, "strokeColor", None) if "text;" not in style else None
                d.rectangle([x, y, x + w, y + h], fill=fill, outline=stroke)
        for cid, g in self.geo.items():
            if g[0] == "edge":
                _, s_, t, style, label, (sx, sy, tx, ty), pts, lpos = g
                poly = [anchor(s_, sx, sy), *pts, anchor(t, tx, ty)]
                d.line(poly, fill=col(style, "strokeColor", "#000"), width=2)
                if label:
                    seg = [((poly[i][0] + poly[i + 1][0]) / 2, (poly[i][1] + poly[i + 1][1]) / 2) for i in range(len(poly) - 1)]
                    a, b = poly[0], poly[-1]
                    f = (lpos + 1) / 2
                    m = seg[len(seg) // 2] if len(poly) > 2 else (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)
                    txt = label.replace("<br>", "\n")
                    for tag in ("<b>", "</b>", "<i>", "</i>"):
                        txt = txt.replace(tag, "")
                    bbox = d.multiline_textbbox(m, txt, anchor="mm")
                    d.rectangle(bbox, fill="white")
                    d.multiline_text(m, txt, fill="black", anchor="mm")
        for cid, g in self.geo.items():
            if g[0] != "edge":
                x, y, w, h, style, label = g
                txt = label.replace("<br>", "\n").replace("<b>", "").replace("</b>", "")
                for tag in ("<i>", "</i>", "<u>", "</u>"):
                    txt = txt.replace(tag, "")
                d.multiline_text((x + 4, y + 3), txt[:400], fill="black")
        img.save(path, format="PNG")


def dc_nodes(p, dc, ox, logical):
    """Place one DC at x-offset ox. Returns dict of cell ids."""
    ids = {}
    asb = 65000 + 100 * dc
    p.box(f"DC{dc} · marpla-DC{dc} · AS {asb}–{asb + 3}" + ("" if logical else f" · mgmt 10.30.{dc}x.x"),
          ox, 60, 1000, 900 if logical else 820, DCBOX)
    for i in (1, 2):
        name = f"marpla-dc-{dc}-s0{i}"
        x = ox + (190 if i == 1 else 600)
        if logical:
            label = (f"<b>{name}</b><br>AS {asb} · Lo0 10.10{dc}.0.{i}<br>VTEP Lo1 10.10{dc}.3.{i}"
                     f"<br>EVPN route server + EVPN GW<br>RD 10.10{dc}.0.{i}:&lt;VLAN|vrf_id&gt; (też domain remote)")
            ids[f"s{i}"] = p.box(label, x, 170, 210, 70, BASE + GW)
        else:
            label = f"<b>{name}</b><br>spine · mgmt 10.30.{dc}1.{i}"
            ids[f"s{i}"] = p.box(label, x, 230, 210, 50, BASE + SPINE)
    zones = [("wew", 1, 65101, 210, 2), ("priv", 3, 65102, 310, 3), ("ext", 5, 65103, 110, 1)]
    for k, (z, first, _, vlan, octet) in enumerate(zones):
        fill, stroke = ZONE[z]
        zx = ox + 20 + k * 325
        zas = asb + 1 + k
        if logical:
            p.box(f"dmz:{z}", zx, 420, 310, 250, f"rounded=1;whiteSpace=wrap;html=1;fillColor={fill};strokeColor={stroke};"
                  "verticalAlign=top;align=left;spacingLeft=6;fontStyle=1;fontSize=12;arcSize=4;")
            vt = f"10.10{dc}.2.{first}"
            loc = int(f"{str(vlan)[0]}2{dc}")
            label = (f"<b>dc{dc}-{z}</b> · AS {zas}<br>MLAG l0{first} + l0{first + 1}<br>VTEP {vt} (shared)"
                     f"<br>VRF {z.upper()} · L3VNI {octet}009000 · RT {octet}0:{octet}0"
                     f"<br><b>VLAN {vlan}</b> → VNI {octet}000{vlan} · RT {vlan}:{vlan} <i>(DCI)</i><br>&nbsp;&nbsp;GW 10.{octet}.10.1"
                     f"<br>VLAN {loc} → VNI {octet}000{loc} · RT {loc}:{loc} <i>(local)</i><br>&nbsp;&nbsp;GW 10.{octet}.2{dc}.1"
                     + ("<br>VLAN 399 → VNI 3000399 <i>(FW HA, L2)</i>" if z == "priv" else ""))
            ids[z] = p.box(label, zx + 15, 450, 280, 200, BASE + f"fillColor=#ffffff;strokeColor={stroke};align=left;spacingLeft=6;")
        else:
            p.box(f"dmz:{z} · AS {zas}", zx, 400, 310, 130, f"rounded=1;whiteSpace=wrap;html=1;fillColor={fill};strokeColor={stroke};"
                  "verticalAlign=top;align=left;spacingLeft=6;fontStyle=1;fontSize=12;arcSize=4;")
            for j in (0, 1):
                n = first + j
                name = f"marpla-dc-{dc}-{z}-l0{n}"
                ids[f"l{n}"] = p.box(f"<b>{name}</b><br>mgmt 10.30.{dc}2.{n}", zx + 10 + j * 155, 445, 135, 60,
                                     BASE + f"fillColor=#ffffff;strokeColor={stroke};")
            a, b = ids[f"l{first}"], ids[f"l{first + 1}"]
            p.edge(a, b, E_MLAG, "", 1, 0.3, 0, 0.3)
            p.edge(a, b, E_MLAG, "", 1, 0.7, 0, 0.7)
    fwy = 760 if logical else 690
    ids["fw"] = p.box(f"<b>marpla-dc-{dc}-fw01</b><br>FW cluster node ({'A' if dc == 1 else 'P'})<br>"
                      f"mgmt 10.30.{dc}9.1 · .1{dc} in zone VLANs", ox + 390, fwy, 220, 60, BASE + FW)
    return ids


def physical():
    p = Page("Fizyczna", 2160, 1180)
    p.box("<b>Dual DC + DCI – topologia fizyczna</b> (containerlab, 18 × cEOS 4.35.6M)", 20, 15, 900, 30,
          TEXT + "fontSize=18;")
    dcs = {dc: dc_nodes(p, dc, 20 if dc == 1 else 1140, False) for dc in (1, 2)}
    for dc, ids in dcs.items():
        for n in range(1, 7):
            lf = ids[f"l{n}"]
            p.edge(lf, ids["s1"], E_PHY, "", 0.3, 0, None, None)
            p.edge(lf, ids["s2"], E_PHY, "", 0.7, 0, None, None)
            p.edge(ids["fw"], lf, E_FW, "", None, None, 0.5, 1)
    a, b = dcs[1], dcs[2]
    ORTH = E_DCI + "edgeStyle=orthogonalEdgeStyle;rounded=0;"
    sp = {k: p.geo[v] for k, v in (("a1", a["s1"]), ("a2", a["s2"]), ("b1", b["s1"]), ("b2", b["s2"]))}

    def dci(src, sx, dst, tx, level, label):
        (x1, y1, w1, _, _, _), (x2, y2, w2, _, _, _) = sp[src], sp[dst]
        p.edge({"a1": a["s1"], "a2": a["s2"]}[src], {"b1": b["s1"], "b2": b["s2"]}[dst], ORTH, label, sx, 0, tx, 0,
               points=[(x1 + w1 * sx, level), (x2 + w2 * tx, level)])

    dci("a1", 0.3, "b1", 0.3, 105, "dc1-s01 Et7 10.100.0.0/31 ↔ dc2-s01 Et7 .1")
    dci("a1", 0.7, "b2", 0.3, 135, "dc1-s01 Et8 10.100.0.2/31 ↔ dc2-s02 Et8 .3")
    dci("a2", 0.3, "b1", 0.7, 165, "dc1-s02 Et8 10.100.0.6/31 ↔ dc2-s01 Et8 .7")
    dci("a2", 0.7, "b2", 0.7, 195, "dc1-s02 Et7 10.100.0.4/31 ↔ dc2-s02 Et7 .5")
    p.box("<b>Okablowanie</b><br>"
          "• leaf Et1 → s01, leaf Et2 → s02; port spine'a = numer leafa (l01 → Et1 … l06 → Et6)<br>"
          "• MLAG peer-link: Et3 + Et4 (żółte)<br>"
          "• leaf Et5 → firewall (LACP, Port-Channel5 na parze MLAG); FW: Et1/2 wew, Et3/4 priv, Et5/6 ext<br>"
          "• DCI (czerwone, grube): 4 × /31 spine ↔ spine, pełna siatka 2 × 2, MTU 9214<br>"
          "• mgmt: sieć containerlab 10.30.0.0/16 (marpla_dualdc_mgmt)",
          20, 900, 1100, 110, TEXT + "fillColor=#ffffff;strokeColor=#999999;spacing=8;")
    p.box("<b>Numery seryjne</b><br>CAFECAFECAFE{dc}101/102 – spine'y<br>CAFECAFECAFE{dc}111–116 – leafy",
          1140, 900, 400, 70, TEXT + "fillColor=#ffffff;strokeColor=#999999;spacing=8;")
    return p


def logical():
    p = Page("Logiczna", 2160, 1460)
    p.box("<b>Dual DC + DCI – topologia logiczna</b> (eBGP underlay + eBGP EVPN, EVPN multi-domain gateway)",
          20, 15, 1200, 30, TEXT + "fontSize=18;")
    dcs = {dc: dc_nodes(p, dc, 20 if dc == 1 else 1140, True) for dc in (1, 2)}
    for dc, ids in dcs.items():
        ox = 20 if dc == 1 else 1140
        p.box(f"<b>EVPN GW domain DC{dc}</b> – all-active multihoming (I-ESI 0000:0000:000{dc}:000{dc}:000{dc}),"
              f" D-path {'65100:1' if dc == 1 else '65200:2'}",
              ox + 170, 120, 660, 140, "rounded=1;whiteSpace=wrap;html=1;fillColor=none;strokeColor=#9673a6;dashed=1;"
              "verticalAlign=top;fontSize=11;arcSize=6;")
        for z in ("wew", "priv", "ext"):
            p.edge(ids[z], ids["s1"], E_UND, "", 0.35, 0, 0.3, 1)
            p.edge(ids[z], ids["s2"], E_UND, "", 0.65, 0, 0.7, 1)
            p.edge(ids[z], ids["s1"], E_EVPN, "", 0.25, 0, 0.15, 1)
            p.edge(ids[z], ids["s2"], E_EVPN, "", 0.75, 0, 0.85, 1)
            p.edge(ids["fw"], ids[z], E_FW, "LACP trunk", None, None, 0.5, 1)
        p.box("<b>RM-UNDERLAY-TO-LEAFS</b> (out do leafów):<br>loopbacki bram drugiego DC nie trafiają do leafów",
              ox + 330, 330, 330, 45, TEXT + "fillColor=#fff2cc;strokeColor=#d6b656;spacing=4;fontSize=10;")
        p.box("VXLAN: leaf ↔ <b>tylko</b> lokalne bramy", ox + 20, 330, 250, 25,
              TEXT + "fontColor=#2d7600;fontStyle=1;fontSize=11;")
    a, b = dcs[1], dcs[2]
    p.edge(a["s2"], b["s1"], E_UND, "eBGP underlay ×4 (/31): tylko Lo0 + VTEP bram<br>PL-DCI-OUT / PL-DCI-IN",
           1, 0.25, 0, 0.25)
    p.edge(a["s2"], b["s1"], E_EVPN, "eBGP EVPN multihop Lo0 ↔ Lo0 (2 × 2)<br>EVPN-OVERLAY-CORE · domain remote",
           1, 0.55, 0, 0.55)
    p.edge(a["s2"], b["s1"], E_VX, "VXLAN GW ↔ GW: tylko VNI DCI<br>1000110 · 2000210 · 3000310 · 3000399",
           1, 0.85, 0, 0.85)
    p.box("<b>Geo-rozciągnięty klaster FW A/P</b> – węzeł A w DC1, węzeł P w DC2; ten sam anycast GW (IP + MAC 00:1c:73:00:dc:99) w obu DC; "
          "HA po VLAN 399 (L2 przez DCI)", 430, 850, 1300, 40,
          "rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;dashed=1;fontSize=12;")
    p.edge(a["fw"], b["fw"], "endArrow=none;html=1;strokeWidth=2;strokeColor=#b85450;dashed=1;", "HA / stretched VLANs przez EVPN GW",
           1, 0.5, 0, 0.5)
    # legend
    lx, ly = 20, 1000
    p.box("<b>Legenda</b>", lx, ly, 560, 190, TEXT + "fillColor=#ffffff;strokeColor=#999999;spacing=8;")
    rows = [(E_UND, "eBGP underlay (IPv4 unicast)"), (E_EVPN, "eBGP EVPN overlay"), (E_VX, "tunele VXLAN"),
            (E_FW, "LACP do firewalla"), (E_DCI, "łącze DCI (strona fizyczna)")]
    for i, (st, txt) in enumerate(rows):
        y = ly + 40 + i * 28
        s = p.box("", lx + 20, y, 1, 1, "text;html=1;")
        t = p.box("", lx + 120, y, 1, 1, "text;html=1;")
        p.edge(s, t, st)
        p.box(txt, lx + 135, y - 9, 400, 20, TEXT)
    # VLAN / VNI table
    tbl = ("<b>Strefy, VLAN-y, VNI</b> (L2VNI = baza strefy + VLAN; ext 100xxxx · wew 200xxxx · priv 300xxxx)"
           "<table border='1' cellpadding='3' style='border-collapse:collapse;font-size:11px;margin-top:6px'>"
           "<tr><th>strefa</th><th>VRF / L3VNI</th><th>VLAN</th><th>VNI</th><th>anycast GW</th><th>zasięg</th></tr>"
           "<tr><td>ext</td><td>EXT 1009000</td><td>110</td><td>1000110</td><td>10.1.10.1/24</td><td>DC1+DC2 (DCI)</td></tr>"
           "<tr><td></td><td></td><td>121 / 122</td><td>1000121 / 1000122</td><td>10.1.21.1 / 10.1.22.1</td><td>lokalne DC1 / DC2</td></tr>"
           "<tr><td>wew</td><td>WEW 2009000</td><td>210</td><td>2000210</td><td>10.2.10.1/24</td><td>DC1+DC2 (DCI)</td></tr>"
           "<tr><td></td><td></td><td>221 / 222</td><td>2000221 / 2000222</td><td>10.2.21.1 / 10.2.22.1</td><td>lokalne DC1 / DC2</td></tr>"
           "<tr><td>priv</td><td>PRIV 3009000</td><td>310</td><td>3000310</td><td>10.3.10.1/24</td><td>DC1+DC2 (DCI)</td></tr>"
           "<tr><td></td><td></td><td>321 / 322</td><td>3000321 / 3000322</td><td>10.3.21.1 / 10.3.22.1</td><td>lokalne DC1 / DC2</td></tr>"
           "<tr><td></td><td></td><td>399</td><td>3000399</td><td>– (FW HA, L2)</td><td>DC1+DC2 (DCI)</td></tr>"
           "</table>")
    p.box(tbl, 620, 1000, 820, 260, TEXT + "spacing=8;fillColor=#ffffff;strokeColor=#999999;")
    p.box("<b>ASN</b><br>DC1: spine'y 65100 · wew 65101 · priv 65102 · ext 65103<br>"
          "DC2: spine'y 65200 · wew 65201 · priv 65202 · ext 65203<br><br>"
          "<b>Pule</b><br>Lo0 spine 10.10{dc}.0.0/24 · Lo0 leaf 10.10{dc}.1.0/24<br>"
          "VTEP leaf 10.10{dc}.2.0/24 · VTEP GW 10.10{dc}.3.0/24<br>uplinki 10.10{dc}.10.0/24 · DCI 10.100.0.0/29",
          1480, 1000, 420, 190, TEXT + "fillColor=#ffffff;strokeColor=#999999;spacing=8;")
    return p


def load_sc():
    import glob, os, yaml
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "avd", "intended", "structured_configs")
    return {os.path.basename(f)[:-4]: yaml.safe_load(open(f)) for f in sorted(glob.glob(base + "/*.yml"))}


def routing_page(dc, sc):
    other = 3 - dc
    p = Page(f"Routing i P2P DC{dc}", 2100, 1700)
    pre = f"marpla-dc-{dc}-"

    def lo(h, n):
        return next(l["ip_address"].split("/")[0] for l in sc[h]["loopback_interfaces"] if l["name"] == n)

    def eth(h):
        return {e["name"]: e for e in sc[h].get("ethernet_interfaces", []) if e.get("ip_address")}

    def vl(h, n):
        return next(v["ip_address"] for v in sc[h]["vlan_interfaces"] if v["name"] == n)

    asn = lambda h: sc[h]["router_bgp"]["as"]
    p.box(f"<b>DC{dc} – route servery EVPN i adresacja P2P</b> (dane z AVD intended/structured_configs)",
          20, 15, 1400, 30, TEXT + "fontSize=18;")
    p.box(f"DC{dc} · AS {asn(pre + 's01')} (spine'y) · underlay eBGP po /31 · overlay eBGP EVPN Lo0 ↔ Lo0",
          20, 60, 1580, 800, DCBOX)
    spines = {}
    for i, x in ((1, 300), (2, 1000)):
        h = f"{pre}s0{i}"
        links = []
        for ifname, e in sorted(eth(h).items(), key=lambda kv: int(kv[0][8:])):
            peer, pif = e["description"].split("_")[1:3]
            pip = eth(peer)[pif]["ip_address"].split("/")[0]
            short = peer.replace(f"marpla-dc-", "dc")
            kind = "DCI " if e["description"].startswith("DCI_") else ""
            links.append(f"{kind}Et{ifname[8:]} {e['ip_address']} ⇄ {short} Et{pif[8:]} {pip}")
        spines[i] = p.box(f"<b>{h}</b> · AS {asn(h)}<br>Lo0 {lo(h, 'Loopback0')} · VTEP {lo(h, 'Loopback1')}"
                          f"<br><b>EVPN Route Server</b> dla leafów DC{dc} (next-hop-unchanged)"
                          f"<br><b>+ EVPN Gateway</b> → DC{other}<br><font style='font-size:10px'>" + "<br>".join(links) + "</font>",
                          x, 190, 340, 205, BASE + GW + "align=left;spacingLeft=6;verticalAlign=top;")
        p.box("RS", x + 310, 175, 44, 30, "ellipse;whiteSpace=wrap;html=1;fillColor=#9673a6;strokeColor=#ffffff;"
              "fontColor=#ffffff;fontStyle=1;fontSize=13;")
    # remote gateways
    p.box(f"DC{other} – zdalna domena EVPN", 1640, 60, 440, 800, DCBOX)
    remote = {}
    for i, y in ((1, 200), (2, 480)):
        h = f"marpla-dc-{other}-s0{i}"
        dl = [f"DCI Et{ifn[8:]} {e['ip_address']} ⇄ {e['description'].split('_')[1].replace('marpla-dc-', 'dc')}"
              for ifn, e in sorted(eth(h).items()) if e["description"].startswith("DCI_")]
        remote[i] = p.box(f"<b>{h}</b> · AS {asn(h)}<br>Lo0 {lo(h, 'Loopback0')} · VTEP {lo(h, 'Loopback1')}"
                          f"<br>RS DC{other} + EVPN Gateway<br><font style='font-size:10px'>" + "<br>".join(dl) + "</font>",
                          1720, y, 340, 95, BASE + GW + "align=left;spacingLeft=6;")
    # DCI links (orthogonal, above the spines, then down the right side)
    ORTH = E_DCI + "edgeStyle=orthogonalEdgeStyle;rounded=0;"
    lvl = {1: 90, 2: 115, 3: 140, 4: 165}
    k = 0
    for i in (1, 2):
        h = f"{pre}s0{i}"
        for ifname, e in sorted(eth(h).items()):
            if not e.get("description", "").startswith("DCI_"):
                continue
            k += 1
            peer = e["description"].split("_")[1]
            j = int(peer[-1])
            pe = eth(peer)[e["description"].split("_")[2]]
            sx = 0.3 if k % 2 else 0.7
            x0, y0, w0, *_ = p.geo[spines[i]]
            xr, yr, wr, hr, *_ = p.geo[remote[j]]
            ty = 0.3 if k <= 2 else 0.7
            col_x = 1660 + 12 * k
            p.edge(spines[i], remote[j], ORTH, "", sx, 0, 0, ty, points=[(x0 + w0 * sx, lvl[k]), (col_x, lvl[k]), (col_x, yr + hr * ty)], lpos=0)
    core = "<br>".join(
        f"{pre}s0{i} ⇄ " + ", ".join(n["ip_address"] for n in sc[f"{pre}s0{i}"]["router_bgp"]["neighbors"]
                                     if n.get("peer_group") == "EVPN-OVERLAY-CORE") for i in (1, 2))
    p.box(f"<b>EVPN-OVERLAY-CORE</b><br>eBGP EVPN multihop (TTL 15), Lo0 ↔ Lo0<br><i>domain remote</i>, D-path<br>{core}"
          f"<br><br><b>DCI underlay</b>: tylko Lo0 + VTEP bram<br>PL-DCI-OUT / PL-DCI-IN",
          1660, 620, 400, 200, TEXT + "fillColor=#ffffff;strokeColor=#9673a6;spacing=6;")
    # leaf pairs
    zones = [("wew", 1), ("priv", 3), ("ext", 5)]
    rows = []
    for zi, (z, first) in enumerate(zones):
        fill, stroke = ZONE[z]
        zx = 40 + zi * 515
        a, b = f"{pre}{z}-l0{first}", f"{pre}{z}-l0{first + 1}"
        p.box(f"dmz:{z} · AS {asn(a)}", zx, 520, 500, 300, f"rounded=1;whiteSpace=wrap;html=1;fillColor={fill};"
              f"strokeColor={stroke};verticalAlign=top;align=left;spacingLeft=6;fontStyle=1;fontSize=12;arcSize=4;")
        leaf = {}
        for j, h in enumerate((a, b)):
            n = int(h[-1])
            ups = []
            for up, si in (("Ethernet1", 1), ("Ethernet2", 2)):
                e, sp = eth(h)[up], f"{pre}s0{si}"
                spi = eth(sp)[f"Ethernet{n}"]
                ups.append((up, e, si, sp, spi))
            leaf[h] = p.box(f"<b>{h}</b> · AS {asn(h)}<br>Lo0 {lo(h, 'Loopback0')} · VTEP {lo(h, 'Loopback1')}"
                            f"<br>EVPN → RS s01, s02<br><font style='font-size:10px'>"
                            + "<br>".join(f"Et{up[-1]} {e['ip_address'].split('/')[0]} ⇄ s0{si} Et{n} {spi['ip_address'].split('/')[0]}"
                                          for up, e, si, sp, spi in ups) + "</font>",
                            zx + 10 + j * 245, 600, 235, 95, BASE + f"fillColor=#ffffff;strokeColor={stroke};align=left;spacingLeft=6;")
            for (up, e, si, sp, spi), ex in zip(ups, (0.25, 0.75)):
                p.edge(leaf[h], spines[si], E_UND, "", ex, 0, n / 7, 1)
                rows.append((h, up, e["ip_address"], sp, f"Ethernet{n}", spi["ip_address"]))
        p.edge(leaf[a], leaf[b], E_MLAG, "", 1, 0.35, 0, 0.35)
        p.edge(leaf[a], leaf[b], E_MLAG, "", 1, 0.65, 0, 0.65)
        p.box(f"<b>MLAG</b> peer-link Po3 (Et3 + Et4)<br>Vlan4094 (MLAG): {vl(a, 'Vlan4094')} ⇄ {vl(b, 'Vlan4094').split('/')[0]}"
              f"<br>Vlan4093 (iBGP L3, AS {asn(a)}): {vl(a, 'Vlan4093')} ⇄ {vl(b, 'Vlan4093').split('/')[0]}",
              zx + 15, 710, 470, 60, TEXT + "fontSize=11;")
        rows.append((a, "Vlan4094 MLAG", vl(a, "Vlan4094"), b, "Vlan4094", vl(b, "Vlan4094")))
        rows.append((a, "Vlan4093 iBGP", vl(a, "Vlan4093"), b, "Vlan4093", vl(b, "Vlan4093")))
    p.box("Leafy: eBGP underlay po /31 do obu spine'ów (IPv4-UNDERLAY-PEERS) + eBGP EVPN Lo0 ↔ Lo0 do obu RS "
          "(EVPN-OVERLAY-PEERS, multihop 3). Spine'y wysyłają do leafów underlay przez RM-UNDERLAY-TO-LEAFS "
          f"(bez loopbacków bram DC{other}).", 40, 465, 1540, 40, TEXT + "fontSize=11;fontColor=#0050ef;")
    # P2P table
    for i in (1, 2):
        h = f"{pre}s0{i}"
        for ifname, e in sorted(eth(h).items()):
            if e.get("description", "").startswith("DCI_"):
                peer, pif = e["description"].split("_")[1:3]
                rows.append((h, f"{ifname} DCI", e["ip_address"], peer, pif, eth(peer)[pif]["ip_address"]))
    tr = "".join(f"<tr><td>{a}</td><td>{b}</td><td>{c}</td><td>{d}</td><td>{e}</td><td>{f}</td></tr>" for a, b, c, d, e, f in rows)
    p.box("<b>Adresacja P2P DC" + str(dc) + "</b> (uplinki, MLAG, DCI)"
          "<table border='1' cellpadding='2' style='border-collapse:collapse;font-size:10px;margin-top:4px'>"
          "<tr><th>urządzenie A</th><th>interfejs</th><th>IP A</th><th>urządzenie B</th><th>interfejs</th><th>IP B</th></tr>"
          + tr + "</table>", 20, 890, 900, 760, TEXT + "spacing=6;fillColor=#ffffff;strokeColor=#999999;")
    p.box("<b>Gdzie są RR?</b><br>Overlay jest eBGP, więc zamiast iBGP route reflectorów rolę „RR” pełnią "
          "<b>route servery EVPN</b> – spine'y każdego DC (purpurowe, znaczek RS). Leafy mają sesje EVPN tylko do nich; "
          "RS przekazują trasy bez zmiany next-hopa (next-hop-unchanged), więc tunele VXLAN idą leaf ↔ leaf w obrębie DC.<br><br>"
          "Ten sam spine jest też <b>EVPN Gateway</b>: trasy z drugiego DC ogłasza leafom z next-hopem = własny VTEP, "
          "więc leafy nie tunelują do drugiego DC.<br><br>"
          f"<b>Pule DC{dc}</b>: Lo0 spine 10.10{dc}.0.0/24 · Lo0 leaf 10.10{dc}.1.0/24 · VTEP leaf 10.10{dc}.2.0/24 · "
          f"VTEP GW 10.10{dc}.3.0/24 · uplinki 10.10{dc}.10.0/24 (wszystkie P2P to /31) · MLAG 10.10{dc}.20.0/24 · MLAG L3 10.10{dc}.21.0/24 · DCI 10.100.0.0/29",
          960, 890, 640, 300, TEXT + "spacing=8;fillColor=#fff2cc;strokeColor=#d6b656;")
    return p


def rdrt_page(sc):
    p = Page("RD i RT", 2160, 1900)
    p.box("<b>RD i RT – schemat i rozgłaszanie tras EVPN przez bramy</b> (dane z AVD structured_configs; ścieżka trasy sprawdzona na labie)",
          20, 15, 1700, 30, TEXT + "fontSize=18;")
    # --- route propagation chain (live trace) ---
    p.box("<b>Przykład:</b> trasa type-2 MAC/IP węzła FW DC1 (10.3.10.11, MAC 001c.7331.18f2) w VLAN 310 / strefa priv – "
          "RT nie zmienia się na całej ścieżce, zmieniają się RD i next-hop na bramach", 20, 60, 2100, 30, TEXT + "fontSize=13;")
    steps = [
        ("dc1-priv-l03 (+ l04)", "leaf, AS 65102", "origin (Local)",
         "RD 10.101.1.3:310 (l04: 10.101.1.4:310)<br>RT 310:310 (MAC-VRF) + 30:30 (VRF PRIV)<br>NH 10.101.2.3 (VTEP MLAG)", ZONE["priv"]),
        ("dc1-s01 / s02", "RS + EVPN GW, AS 65100", "re-origination → domain remote",
         "lokalnie: przekazuje bez zmian (next-hop-unchanged)<br>do DC2: <b>RD 10.101.0.1:310</b> (s02: 10.101.0.2:310)<br>"
         "RT 310:310 + 30:30<br><b>NH 10.101.3.1</b> (VTEP bramy)", ("#e1d5e7", "#9673a6")),
        ("dc2-s01 / s02", "RS + EVPN GW, AS 65200", "re-origination → domain local",
         "odbiera jako <i>remote</i> (RD 10.101.0.x:310)<br>do leafów DC2: <b>RD 10.102.0.1:310</b> (s02: 10.102.0.2:310)<br>"
         "RT 310:310 + 30:30<br><b>NH 10.102.3.1</b>", ("#e1d5e7", "#9673a6")),
        ("dc2-priv-l03 / l04", "leaf, AS 65202", "import",
         "widzi tylko RD bram DC2 (10.102.0.1:310, 10.102.0.2:310)<br>import po RT 310:310 → VLAN 310, 30:30 → VRF PRIV<br>"
         "NH 10.102.3.1 / 10.102.3.2 – tunel VXLAN tylko do bram DC2", ZONE["priv"]),
    ]
    prev = None
    for i, (name, role, what, body, (fill, stroke)) in enumerate(steps):
        b = p.box(f"<b>{name}</b><br><i>{role}</i><br><u>{what}</u><br><br>{body}", 30 + i * 545, 100, 400, 170,
                  BASE + f"fillColor={fill};strokeColor={stroke};align=left;spacingLeft=8;verticalAlign=top;")
        if prev:
            p.edge(prev, b, "endArrow=classic;html=1;strokeWidth=3;strokeColor=#2d7600;",
                   ["eBGP EVPN<br>EVPN-OVERLAY-PEERS", "eBGP EVPN multihop<br>EVPN-OVERLAY-CORE<br>(DCI)", "eBGP EVPN<br>EVPN-OVERLAY-PEERS"][i - 1])
        prev = b
    # --- RT table ---
    s1 = sc["marpla-dc-1-s01"]["router_bgp"]
    gw_vlans = {v["id"] for v in s1["vlans"]}
    rows, vrfs = [], {}
    for h, c in sc.items():
        for v in c["router_bgp"].get("vrfs", []):
            vrfs[v["name"]] = v["route_targets"]["import"][0]["route_targets"][0]
    vx = {}
    for h, c in sc.items():
        for v in c.get("vxlan_interface", {}).get("vxlan1", {}).get("vxlan", {}).get("vlans", []):
            vx[v["id"]] = v["vni"]
    vrf_vni = {v["name"]: v["vni"] for c in sc.values() for v in c.get("vxlan_interface", {}).get("vxlan1", {}).get("vxlan", {}).get("vrfs", [])}
    zone_of_vlan = lambda vid: {"1": "ext", "2": "wew", "3": "priv"}[str(vid)[0]]
    for vrf in ("EXT", "WEW", "PRIV"):
        rows.append(f"<tr style='background:#f0f0f0'><td><b>{vrf.lower()}</b></td><td>VRF {vrf} (IP-VRF, type-5)</td><td>{vrf_vni[vrf]}</td>"
                    f"<td><b>{vrfs[vrf]}</b></td><td>{vrfs[vrf]}</td><td>wszystkie leafy strefy + bramy</td></tr>")
        for vid in sorted(k for k in vx if zone_of_vlan(k) == vrf.lower()):
            dci = vid in gw_vlans
            rows.append(f"<tr><td></td><td>VLAN {vid} (MAC-VRF, type-2/3)</td><td>{vx[vid]}</td><td><b>{vid}:{vid}</b></td>"
                        f"<td>{f'{vid}:{vid}' if dci else '– (nie idzie przez DCI)'}</td>"
                        f"<td>{'leafy strefy w DC1 + DC2, bramy' if dci else ('tylko DC1' if str(vid)[2] == '1' else 'tylko DC2')}</td></tr>")
    p.box("<b>Route Targets</b> – identyczne w DC1 i DC2 (te same definicje tenantów), unikalne per strefa"
          "<table border='1' cellpadding='3' style='border-collapse:collapse;font-size:11px;margin-top:6px'>"
          "<tr><th>strefa</th><th>instancja</th><th>VNI</th><th>RT (import/export)</th><th>RT evpn domain remote (bramy)</th><th>gdzie</th></tr>"
          + "".join(rows) + "</table>", 20, 300, 1080, 560, TEXT + "spacing=8;fillColor=#ffffff;strokeColor=#999999;")
    # --- explanation ---
    p.box("<b>Jak są budowane</b><br>"
          "• <b>RD MAC-VRF</b> = &lt;Lo0 router-id&gt;:&lt;VLAN ID&gt; – np. 10.101.1.3:310<br>"
          "• <b>RD IP-VRF</b> = &lt;Lo0&gt;:&lt;vrf_id&gt; – EXT 10, WEW 20, PRIV 30 – np. 10.101.1.3:30<br>"
          "• <b>RT MAC-VRF</b> = &lt;VLAN&gt;:&lt;VLAN&gt;, <b>RT IP-VRF</b> = &lt;vrf_id&gt;:&lt;vrf_id&gt;<br>"
          "&nbsp;&nbsp;(mac_vrf_id_base: 0 – 7-cyfrowe VNI nie zmieściłyby się w RD typu IP:liczba)<br>"
          "• RD jest unikalny per urządzenie (Lo0), RT wspólny dla całej strefy w obu DC<br><br>"
          "<b>Bramy (spine'y)</b><br>"
          "• <code>rd evpn domain remote</code> = ten sam &lt;Lo0&gt;:&lt;id&gt; – RD tras ogłaszanych do drugiego DC<br>"
          "• <code>route-target import export evpn domain remote</code> = ten sam RT – tylko VLAN-y DCI: 110, 210, 310, 399<br>"
          "• type-5 (IP-VRF) przechodzi przez <i>next-hop-self … inter-domain</i> z RT VRF-u<br>"
          "• domain identifier (D-path): DC1 <b>65100:1</b>, DC2 <b>65200:2</b> – zapobiega zapętleniu tras między domenami<br>"
          "• all-active multihoming bram: ES DC1 0000:0000:0001:0001:0001, ES-import RT 00:00:00:01:00:01;<br>"
          "&nbsp;&nbsp;DC2 0000:0000:0002:0002:0002, ES-import RT 00:00:00:02:00:02<br><br>"
          "<b>Separacja stref</b>: leaf importuje tylko RT swojej strefy, więc VRF-y innych stref nie dostają tras. "
          "Bez RTC (gałąź <i>single-domain</i>) trasy innych stref nadal docierają do tablicy BGP leafa – nie są tylko importowane.",
          1130, 300, 1000, 560, TEXT + "spacing=8;fillColor=#fff2cc;strokeColor=#d6b656;")
    # --- RD per device ---
    drows = []
    for h in sorted(sc, key=lambda x: (x.split("-")[2], not x.split("-")[3].startswith("s"), x)):
        b = sc[h]["router_bgp"]
        lo0 = next(l["ip_address"].split("/")[0] for l in sc[h]["loopback_interfaces"] if l["name"] == "Loopback0")
        mac = ", ".join(f"{v['rd']}" for v in b.get("vlans", []))
        ip = ", ".join(f"{v['name']} {v['rd']}" for v in b.get("vrfs", []))
        rem = ", ".join(v["rd_evpn_domain"]["rd"] for v in b.get("vlans", []) if v.get("rd_evpn_domain"))
        role = "RS + GW" if h.split("-")[3].startswith("s") else "leaf " + h.split("-")[3]
        drows.append(f"<tr><td>{h}</td><td>{role}</td><td>{lo0}</td><td>{mac}</td><td>{ip}</td><td>{rem or '–'}</td></tr>")
    p.box("<b>Route Distinguishers per urządzenie</b>"
          "<table border='1' cellpadding='3' style='border-collapse:collapse;font-size:10px;margin-top:6px'>"
          "<tr><th>urządzenie</th><th>rola</th><th>Lo0</th><th>RD MAC-VRF (VLAN)</th><th>RD IP-VRF</th><th>RD domain remote</th></tr>"
          + "".join(drows) + "</table>", 20, 890, 2110, 640, TEXT + "spacing=8;fillColor=#ffffff;strokeColor=#999999;")
    return p


sc = load_sc()
pages = [physical(), logical(), routing_page(1, sc), routing_page(2, sc), rdrt_page(sc)]
with open(OUT, "w", encoding="utf-8") as f:
    f.write('<mxfile host="app.diagrams.net" type="device">' + "".join(pg.xml() for pg in pages) + "</mxfile>\n")
if Image is not None and os.environ.get("DRAWIO_PREVIEW"):
    for pg in pages:
        pg.preview(PREV.format(pg.name.replace(" ", "_")))
print("ok", OUT, [len(pg.cells) for pg in pages])
