# Dual DC + DCI – EVPN multi-domain gateway (gałąź rozwojowa)

> **Gałąź `dualDCandDCI`** – gałąź rozwojowa labu dual DC. Konfiguracja labu jest **identyczna jak
> w `single-domain`** (wspólne bramy EVPN dla wszystkich stref, bez RT Constraint); dodatkowo zawiera
> pełny diagram draw.io ze stroną „RD i RT”. Z niej wyrosły gałęzie wariantów.

| Gałąź | Zawartość |
|---|---|
| `main` | lab jednego DC (L2LS, EVPN MLAG) + CVaaS |
| **`dualDCandDCI`** | **ta gałąź**: dual DC bez RTC + pełna dokumentacja draw.io (fizyczna, logiczna, P2P per DC, RD/RT) |
| `single-domain` | ta sama konfiguracja labu – punkt odniesienia wariantu bez RTC |
| `single-domain-with-rtc` | jak `single-domain` + RT Constraint (leaf dostaje tylko trasy EVPN swojej strefy) |

## Jak są rozdzielone strefy

Każda strefa (`wew`, `priv`, `ext`) to osobny tenant/VRF z własnymi route-targetami (VRF 10:10 / 20:20 / 30:30,
VLAN-y `<VLAN>:<VLAN>`), bez przecieków między VRF-ami. Tablice routingu leafów zawierają więc tylko
prefiksy własnej strefy (lokalne i z tej samej strefy w drugim DC), a ruch między strefami może przejść
wyłącznie przez firewall.

**Płaszczyzna sterowania nie jest jednak rozdzielona.** Route servery EVPN (spine'y) wysyłają każdemu
leafowi trasy wszystkich stref; leaf odrzuca obce dopiero przy imporcie do VRF, ale trzyma je w tablicy BGP:

| Urządzenie | ścieżki EVPN z RT w tablicy BGP | w tym wyłącznie z RT innych stref |
|---|---|---|
| `marpla-dc-1-priv-l03` | 144 | 104 |
| `marpla-dc-2-ext-l05` | 150 | 116 |

To ograniczenie usuwa gałąź `single-domain-with-rtc` (RT Constraint: odpowiednio 40 i 34 ścieżki,
wszystkie z RT własnej strefy). Bramy w obu wariantach znają wszystkie strefy, bo obsługują DCI dla każdej z nich.

![Płaszczyzna sterowania bez RTC](dual_dc/docs/control-plane.png)

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
| RTC | wyłączony (`evpn_overlay_bgp_rtc` nieustawione) |
| Tagi CloudVision | `owner:marpla`, `dmz:<strefa>`; hierarchia `marpla-DCx` → `marpla-DCx-POD1` → rack = para leafów |

Pełny opis (VLAN-y, adresacja, okablowanie, pliki): [dual_dc/README.md](dual_dc/README.md);
diagram edytowalny (fizyczny, logiczny, P2P per DC, RD i RT ze ścieżką trasy przez bramy): [dual_dc/topology.drawio](dual_dc/topology.drawio).

## Uruchomienie

```bash
cd dual_dc
make start        # containerlab: 18 × cEOS 4.35.6M, sieć mgmt 10.30.0.0/16
make build        # AVD (DC1 i DC2 jako osobne fabrici) + katalog testów DCI
make deploy_cvp   # przez CVaaS, change control zatwierdzany i uruchamiany automatycznie – albo: make deploy (eAPI)
make test         # fw_test + ANTA: katalogi AVD i testy BGP/EVPN/DCI
make test_dci     # fw_test + tylko testy BGP/EVPN/DCI
make stop         # po decommission urządzeń w CVaaS
```

Obraz cEOS: `./get_ceos.sh -v 4.35.6M` (wymaga `ARISTA_TOKEN`). Raporty ANTA: `dual_dc/avd/anta/reports/`.

## Wyniki testów

Uruchomione 2026-10-06 na labie z wdrożoną konfiguracją gałęzi `single-domain` (`make deploy_cvp`, potem `make test`) –
konfiguracja labu w obu gałęziach jest identyczna (`git diff single-domain dualDCandDCI -- dual_dc/avd dual_dc/clab` jest pusty).

**`fw_test`** – 20/20 celów osiągalnych: z obu węzłów FW anycast GW w każdej strefie (VLAN rozciągnięty
i lokalny), drugi węzeł FW przez DCI w każdej strefie oraz VLAN HA 399.

**Testy BGP/EVPN/DCI** (`dual_dc/avd/anta_catalogs/dci_tests.yml`) – **104/104**:

| Test | Wynik | Co potwierdza |
|---|---|---|
| `VerifyBGPPeerSession`, `VerifyBGPPeerCount` | 32/32 | wszystkie sesje BGP, liczba peerów EVPN i IPv4 |
| `VerifyVxlanVtep` | 16/16 | leafy tunelują tylko do bram własnego DC |
| `VerifyVxlanVniBinding` | 16/16 | przez DCI idą tylko wybrane VNI |
| `VerifyEVPNType5Routes`, `VerifyEVPNType2Route` | 32/32 | trasy przechodzą przez bramy między DC |
| `VerifyBgpRouteMaps`, `VerifyBGPExchangedRoutes` | 8/8 | DCI wymienia tylko loopbacki bram, filtr do leafów działa |

Testów RTC tu nie ma – po uruchomieniu katalogu z gałęzi `single-domain-with-rtc` na tej konfiguracji
28 testów RTC jest czerwonych (brak sesji rt-membership, trasy innych stref w tablicach leafów).

**Pełny `make test`** (katalogi AVD + DCI) – 500 testów: **456 OK, 44 znane odstępstwa**, wszystkie
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
