# Dual DC + DCI – EVPN multi-domain gateway z RT Constraint

> **Gałąź `single-domain-with-rtc`** – dwa ośrodki ze wspólnymi bramami EVPN dla wszystkich stref
> bezpieczeństwa **oraz BGP Route Target Constraint (RFC 4684)**: leaf dostaje w płaszczyźnie
> sterowania wyłącznie trasy EVPN swojej strefy.

| Gałąź | Zawartość |
|---|---|
| `main` | lab jednego DC (L2LS, EVPN MLAG) + CVaaS |
| `dualDCandDCI` | gałąź rozwojowa dual DC – stan bez RTC z pełną dokumentacją (draw.io) |
| `single-domain` | dual DC, wspólne bramy, **bez RTC** – strefy rozdzielone tylko VRF/RT |
| **`single-domain-with-rtc`** | **ta gałąź**: jak `single-domain` + RT Constraint |

## Co wyróżnia tę gałąź

W `single-domain` strefy są rozdzielone tylko w tablicach routingu (osobne VRF-y i route-targety),
ale route servery EVPN (spine'y) wysyłają każdemu leafowi trasy **wszystkich** stref – leaf odrzuca je
dopiero przy imporcie. Tu każdy leaf ogłasza po `address-family rt-membership`, które RT importuje,
a route server wysyła mu tylko pasujące trasy:

```yaml
# dual_dc/avd/group_vars/MARPLA_DCS.yml
evpn_overlay_bgp_rtc: true
```

| | bez RTC (`single-domain`) | z RTC (ta gałąź) |
|---|---|---|
| ścieżki EVPN w tablicy BGP `marpla-dc-1-priv-l03` | 144, z czego 104 wyłącznie z RT stref ext/wew | **40**, każda z RT strefy priv |
| ścieżki EVPN `marpla-dc-2-ext-l05` | 150, z czego 116 obcych | **34** |
| bramy (spine'y) | wszystkie strefy | wszystkie strefy – z założenia obsługują DCI dla każdej |

Bramy pozostają jedynym miejscem, gdzie spotykają się wszystkie strefy (nadal rozdzielone VRF-ami);
pełne rozdzielenie także tam wymagałoby osobnych bram/DCI per strefa.

![Płaszczyzna sterowania z RTC](dual_dc/docs/control-plane.png)

## Topologia

Dwa ośrodki z niezależnym underlayem (eBGP) i overlayem (eBGP EVPN). Każdy ma 2 spine'y (route servery
EVPN i bramy EVPN multi-domain) oraz 3 pary MLAG leafów – po jednej na strefę `wew`, `priv`, `ext`.
DCI to 4 łącza /31 między spine'ami. Do każdej strefy w obu ośrodkach podłączony jest węzeł
geo-rozciągniętego klastra firewall A/P.

![Topologia fizyczna](dual_dc/docs/topology-physical.png)

![Topologia logiczna](dual_dc/docs/topology-logical.png)

## Konfiguracja w skrócie

| Element | Wartość |
|---|---|
| ASN | DC1: spine'y 65100, pary leafów 65101 (wew) / 65102 (priv) / 65103 (ext); DC2: 65200, 65201–65203 |
| Underlay DCI | eBGP po 4 × /31, prefix-listy `PL-DCI-IN/OUT` – tylko Lo0 + VTEP bram |
| Overlay DCI | eBGP EVPN multihop Lo0 ↔ Lo0 między bramami, `domain remote`, D-path 65100:1 / 65200:2 |
| Bramy | spine'y = VTEP + EVPN GW (L2 + L3 inter-domain), all-active multihoming (I-ESI), bez MLAG |
| Filtr do leafów | `RM-UNDERLAY-TO-LEAFS` – loopbacki bram drugiego DC zostają na bramach |
| Przez DCI | tylko VNI: 1000110, 2000210, 3000310, 3000399 |
| L2VNI | baza strefy + VLAN: ext 100xxxx, wew 200xxxx, priv 300xxxx |
| VRF / L3VNI / RT | EXT 1009000 / 10:10 · WEW 2009000 / 20:20 · PRIV 3009000 / 30:30 |
| RD / RT VLAN | RD `<Lo0>:<VLAN>`, RT `<VLAN>:<VLAN>`; VRF: RD `<Lo0>:<vrf_id>` |
| Anycast GW | ten sam IP i MAC `00:1c:73:00:dc:99` w obu DC |
| RTC | `address-family rt-membership` na sesjach EVPN; route servery `default-route-target only` |
| Tagi CloudVision | `owner:marpla`, `dmz:<strefa>`; hierarchia `marpla-DCx` → `marpla-DCx-POD1` → rack = para leafów |

Pełny opis (VLAN-y, adresacja, okablowanie, pliki): [dual_dc/README.md](dual_dc/README.md);
diagram edytowalny ze stronami P2P i RD/RT: [dual_dc/topology.drawio](dual_dc/topology.drawio).

## Uruchomienie

```bash
cd dual_dc
make start        # containerlab: 18 × cEOS 4.35.6M, sieć mgmt 10.30.0.0/16
make build        # AVD (DC1 i DC2 jako osobne fabrici) + katalog testów DCI
make deploy_cvp   # przez CVaaS, change control zatwierdzany i uruchamiany automatycznie – albo: make deploy (eAPI)
make test         # fw_test + ANTA: katalogi AVD i testy BGP/EVPN/DCI/RTC
make test_dci     # fw_test + tylko testy BGP/EVPN/DCI/RTC
make stop         # po decommission urządzeń w CVaaS
```

Obraz cEOS: `./get_ceos.sh -v 4.35.6M` (wymaga `ARISTA_TOKEN`). Raporty ANTA: `dual_dc/avd/anta/reports/`.

## Wyniki testów

Uruchomione 2026-10-06 na labie z wdrożoną konfiguracją tej gałęzi (`make test`).

**`fw_test`** – 20/20 celów osiągalnych: z obu węzłów FW anycast GW w każdej strefie (VLAN rozciągnięty
i lokalny), drugi węzeł FW przez DCI w każdej strefie oraz VLAN HA 399.

**Testy BGP/EVPN/DCI/RTC** (`dual_dc/avd/anta_catalogs/dci_tests.yml`) – **116/116**:

| Test | Wynik | Co potwierdza |
|---|---|---|
| `VerifyBGPPeerSession`, `VerifyBGPPeerCount` | 32/32 | wszystkie sesje BGP; liczba peerów EVPN, IPv4 i **rt-membership** (2 na leafie, 8 na bramie) |
| `VerifyEVPNRoutesMatchImportedRT` (własny test) | 12/12 | tablica BGP EVPN leafa zawiera tylko trasy z RT jego strefy |
| `VerifyVxlanVtep` | 16/16 | leafy tunelują tylko do bram własnego DC |
| `VerifyVxlanVniBinding` | 16/16 | przez DCI idą tylko wybrane VNI |
| `VerifyEVPNType5Routes`, `VerifyEVPNType2Route` | 32/32 | trasy przechodzą przez bramy między DC |
| `VerifyBgpRouteMaps`, `VerifyBGPExchangedRoutes` | 8/8 | DCI wymienia tylko loopbacki bram, filtr do leafów działa |

Bez RTC (kontrola negatywna) 28 testów RTC było czerwonych – testy faktycznie wykrywają brak filtrowania.

**Pełny `make test`** (katalogi AVD + DCI) – 512 testów: **468 OK, 44 znane odstępstwa**, wszystkie
wynikające ze środowiska cEOS lub z projektu, nie z błędu konfiguracji:

| Test | Liczba | Przyczyna |
|---|---|---|
| `VerifyLoggingErrors` | 16 | cEOS-lab loguje przy starcie `HARDWARE-0-SYSTEM_IDENTIFICATION_FAILED` |
| `VerifyInterfaceDiscards` | 16 | odrzucane pakiety na `Management1` (sieć zarządzania Dockera) |
| `VerifyVxlanConfigSanity` | 12 | VLAN-y lokalne (x21/x22) istnieją tylko na jednej parze leafów, więc ich flood list jest pusta – EOS raportuje to jako ostrzeżenie; VLAN-y rozciągnięte mają poprawną flood list (bramy) |

Pozostałe kategorie (BGP, MLAG, routing, STP, łączność, system, konfiguracja) – bez błędów.

## Lab jednego DC

Lab z gałęzi `main` (`clab/`, `avd_inventory/`, `Makefile` w katalogu głównym) jest nadal w repozytorium
bez zmian – jego opis jest w README na gałęzi `main`.
