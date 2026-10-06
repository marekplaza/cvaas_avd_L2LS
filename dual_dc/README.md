# Dual DC + DCI – multi-domain (bramy EVPN per strefa)

Dwa ośrodki (DC1, DC2) z niezależnym underlayem i overlayem, połączone przez DCI między spine'ami.
Każdy ośrodek ma 2 spine'y i 3 pary MLAG leafów – po jednej na strefę bezpieczeństwa `wew`, `priv`, `ext`.
Do każdej pary leafów w obu ośrodkach podłączony jest węzeł geo-rozciągniętego klastra firewall A/P.

## Założenia

| Element | Realizacja |
|---|---|
| Underlay w DC | eBGP, spine ↔ leaf |
| Overlay w DC | eBGP EVPN, spine'y jako route servery (domyślny typ węzła AVD: bez VTEP, bez VRF-ów) |
| ASN | DC1: spine'y 65100, pary leafów 65101 (wew), 65102 (priv), 65103 (ext); DC2: 65200, 65201–65203 |
| Bramy EVPN | **para leafów każdej strefy** (`evpn_gateway` na `node_group`, L2 + L3 inter-domain); każda strefa = osobna domena EVPN |
| DCI overlay | eBGP EVPN multihop para ↔ para tej samej strefy (`EVPN-OVERLAY-CORE`, `domain remote`) – osobne sesje dla wew, priv, ext |
| DCI underlay | 4 łącza /31 spine ↔ spine (pełna siatka 2×2), eBGP; prefix-listy `PL-DCI-IN/OUT` przepuszczają **tylko loopbacki leafów** (Lo0 i VTEP) |
| Izolacja | tunele VXLAN przez DCI tylko para ↔ para tej samej strefy; spine'y nie mają VXLAN ani VRF-ów |
| RT Constraint | `evpn_overlay_bgp_rtc: true` + `RM-RTC-LOCAL-ONLY` (out w `rt-membership`): brama ogłasza tylko członkostwo, które sama generuje – inaczej `0/0` route serverów przechodziłoby przez DCI |
| VNI przez DCI | L2 tylko 110, 210, 310, 399 – VLAN-y lokalne mają `evpn_l2_multi_domain: false`; L3 (type-5) wszystkich podsieci strefy |
| D-path / ES | brak – AVD generuje je tylko z all-active multihoming (niedostępne z MLAG); pętlę blokuje AS path pary |
| Anycast gateway | ten sam IP i MAC (`00:1c:73:00:dc:99`) w obu ośrodkach |

## Strefy, VLAN-y i VNI

L2VNI = baza strefy + VLAN ID (`ext` 100xxxx, `wew` 200xxxx, `priv` 300xxxx).

| Strefa | VRF (L3VNI) | VLAN | Nazwa | Podsieć / anycast GW | VNI | Zasięg |
|---|---|---|---|---|---|---|
| ext | EXT (1009000) | 110 | EXT_FW | 10.1.10.1/24 | 1000110 | DC1 + DC2 (DCI) |
| | | 121 | EXT_DC1_LOCAL | 10.1.21.1/24 | 1000121 | tylko DC1 |
| | | 122 | EXT_DC2_LOCAL | 10.1.22.1/24 | 1000122 | tylko DC2 |
| wew | WEW (2009000) | 210 | WEW_FW | 10.2.10.1/24 | 2000210 | DC1 + DC2 (DCI) |
| | | 221 / 222 | WEW_DC1/DC2_LOCAL | 10.2.21.1 / 10.2.22.1 | 2000221 / 2000222 | lokalne |
| priv | PRIV (3009000) | 310 | PRIV_FW | 10.3.10.1/24 | 3000310 | DC1 + DC2 (DCI) |
| | | 321 / 322 | PRIV_DC1/DC2_LOCAL | 10.3.21.1 / 10.3.22.1 | 3000321 / 3000322 | lokalne |
| | | 399 | FW_HA (tylko L2) | – | 3000399 | DC1 + DC2 (DCI) |

## Urządzenia

| Hostname | Rola | Mgmt IP | Tagi CloudVision |
|---|---|---|---|
| marpla-dc-1-s01 / s02 | spine, route server EVPN DC1 | 10.30.11.1 / .2 | owner:marpla |
| marpla-dc-1-wew-l01 / l02 | leaf MLAG + brama EVPN strefy wew | 10.30.12.1 / .2 | owner:marpla, dmz:wew |
| marpla-dc-1-priv-l03 / l04 | leaf MLAG + brama EVPN strefy priv | 10.30.12.3 / .4 | owner:marpla, dmz:priv |
| marpla-dc-1-ext-l05 / l06 | leaf MLAG + brama EVPN strefy ext | 10.30.12.5 / .6 | owner:marpla, dmz:ext |
| marpla-dc-2-* | lustrzane odbicie DC1 | 10.30.21.x / 10.30.22.x | jw. |
| marpla-dc-1-fw01 / marpla-dc-2-fw01 | węzły klastra FW (cEOS jako host, poza AVD/CVaaS) | 10.30.19.1 / 10.30.29.1 | – |

Hierarchia w CloudVision: `marpla-DC1` / `marpla-DC2` → `marpla-DCx-POD1` → rack = para leafów (`dc1-wew`, `dc1-priv`, …).

## Okablowanie

- leaf `Ethernet1`/`Ethernet2` → spine s01/s02, port spine'a = numer leafa (l01 → `Ethernet1` … l06 → `Ethernet6`)
- MLAG peer-link: `Ethernet3`, `Ethernet4`
- leaf `Ethernet5` → firewall (LACP, Port-Channel5 po stronie leafów)
- DCI: dc1-s01 `Et7` ↔ dc2-s01 `Et7`, dc1-s01 `Et8` ↔ dc2-s02 `Et8`, dc1-s02 `Et7` ↔ dc2-s02 `Et7`, dc1-s02 `Et8` ↔ dc2-s01 `Et8`

## Użycie

```bash
cd dual_dc
make start        # containerlab (18 x cEOS 4.35.6M, sieć mgmt 10.30.0.0/16)
make build        # AVD: dwa niezależne fabrici (MARPLA_DC1, MARPLA_DC2)
make deploy_cvp   # wdrożenie przez CVaaS (albo: make deploy - eAPI)
make test         # fw_test + ANTA: katalogi AVD i testy BGP/EVPN/DCI
make test_dci     # fw_test + tylko testy BGP/EVPN/DCI
make fw_test      # tylko test płaszczyzny danych z węzłów FW
make stop
```

Tokeny CVaaS są współdzielone z labem jednego DC (`../clab/cv-onboarding-token`, `../clab/cv-api-token`).

## Testy

`make build` generuje też `avd/anta_catalogs/dci_tests.yml` (skrypt `avd/gen_dci_catalog.py`) –
oczekiwane wartości są brane z wygenerowanych przez AVD `structured_configs`, więc testy nadążają za zmianami.

| Urządzenia | Test ANTA | Co sprawdza |
|---|---|---|
| wszystkie | `VerifyBGPPeerSession`, `VerifyBGPPeerCount` | wszystkie sesje BGP Established; liczba peerów EVPN, rt-membership i IPv4 (leaf: 2 RS + 2 bramy tej samej strefy w drugim DC) |
| spine'y | `VerifyBgpRouteMaps` | route-mapy DCI (in/out) |
| spine'y | `VerifyBGPExchangedRoutes` | przez DCI ogłaszane/odbierane są loopbacki leafów (Lo0 + VTEP), z obu łączy |
| leafy | `VerifyVxlanVtep` | jedyny zdalny VTEP = para tej samej strefy w drugim DC |
| leafy | `VerifyVxlanVniBinding` | tylko VNI strefy |
| leafy | `VerifyEVPNType5Routes` | podsieć lokalna tej samej strefy z drugiego DC dociera jako type-5 |
| leafy | `VerifyEVPNRoutesMatchImportedRT` (własny, `avd/anta_custom/marpla_tests.py`) | każda ścieżka EVPN w tablicy BGP ma RT strefy leafa – brak tras innych stref |
| leafy | `VerifyEVPNType2Route` | MAC/IP węzła FW z drugiego DC w rozciągniętym VLAN-ie (wymaga ruchu – dlatego `make test` najpierw uruchamia `fw_test`) |

`make fw_test` (`fw_test.sh`) z każdego węzła FW, w każdej strefie: ping anycast GW (VLAN rozciągnięty
i lokalny), ping drugiego węzła FW przez DCI oraz ping po VLAN-ie HA 399. Wynik PASS/FAIL per cel.

Raporty ANTA: `avd/anta/reports/` (poza repo).

## Pliki

| Plik | Zawartość |
|---|---|
| `avd/inventory.yml` | grupy: ośrodki, strefy (`ZONE_*` → tag `dmz`), usługi, firewalle |
| `avd/group_vars/MARPLA_DCS.yml` | wspólne: typ węzła spine (VTEP + usługi), mgmt, AAA, TerminAttr, tagi |
| `avd/group_vars/MARPLA_DC1.yml`, `MARPLA_DC2.yml` | ASN-y, pule IP, pary leafów, łącza DCI, brama EVPN, prefix-listy DCI |
| `avd/group_vars/MARPLA_NETWORK_SERVICES.yml` | tenanty/VRF-y/VLAN-y stref |
| `avd/group_vars/MARPLA_CONNECTED_ENDPOINTS.yml` | podłączenie węzłów firewall |
| `avd/group_vars/ZONE_*.yml` | tag `dmz:<strefa>` |
| `avd/gen_dci_catalog.py`, `avd/anta_catalogs/` | generator i katalog testów BGP/EVPN/DCI |
| `avd/anta_custom/marpla_tests.py` | własny test ANTA dla RTC |
| `fw_test.sh` | test płaszczyzny danych z węzłów FW |
| `docs/*.png`, `tools/gen_png.py` | schematy PNG do README (generator: matplotlib) |
| `topology.drawio`, `tools/gen_drawio.py` | diagram edytowalny (fizyczny, logiczny, P2P per DC, RD/RT) |
| `clab/` | topologia, init-configi, numery seryjne `CAFECAFECAFE{dc}1xx` |

Węzły firewall to cEOS bez routingu, z SVI w każdej strefie (`.11` w DC1, `.12` w DC2). Nie emulują
mechanizmu A/P – służą do sprawdzenia rozciągnięcia L2 i anycast gatewaya przez DCI.
