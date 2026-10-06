# Dual DC + DCI – EVPN multi-domain gateway (single domain, bez RTC)

> **Gałąź `single-domain`** – dwa ośrodki ze wspólnymi bramami EVPN dla wszystkich stref
> bezpieczeństwa. Strefy są rozdzielone osobnymi VRF-ami i route-targetami; **RT Constraint nie jest
> włączony** – to punkt odniesienia dla gałęzi `single-domain-with-rtc`.

| Gałąź | Zawartość |
|---|---|
| `main` | lab jednego DC (L2LS, EVPN MLAG) + CVaaS |
| `dualDCandDCI` | gałąź rozwojowa dual DC – ta sama konfiguracja co tutaj + pełna dokumentacja draw.io (strona RD/RT) |
| **`single-domain`** | **ta gałąź**: dual DC, wspólne bramy, bez RTC |
| `single-domain-with-rtc` | jak ta gałąź + RT Constraint (leaf dostaje tylko trasy EVPN swojej strefy) |

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

### Które RT należą do której strefy

Route-targety są takie same w DC1 i DC2. RT VRF-u (`<vrf_id>:<vrf_id>`) niosą trasy type-5 (prefiksy IP)
i – razem z RT VLAN-u – trasy type-2 MAC/IP; RT VLAN-u (`<VLAN>:<VLAN>`) niosą trasy type-2/type-3 danego segmentu L2.
Ostatnia część RD trasy (`<Lo0>:<VLAN>` lub `<Lo0>:<vrf_id>`) wskazuje ten sam numer, więc strefę widać od razu po RD.

| Strefa | RT VRF (L3VNI) | RT VLAN-ów |
|---|---|---|
| `ext` | `10:10` – VRF EXT (1009000) | `110:110` FW, rozciągnięty · `121:121` lokalny DC1 · `122:122` lokalny DC2 |
| `wew` | `20:20` – VRF WEW (2009000) | `210:210` FW, rozciągnięty · `221:221` lokalny DC1 · `222:222` lokalny DC2 |
| `priv` | `30:30` – VRF PRIV (3009000) | `310:310` FW, rozciągnięty · `321:321` lokalny DC1 · `322:322` lokalny DC2 · `399:399` FW HA |

Leaf strefy `priv` importuje więc tylko `30:30`, `310:310`, `321:321` (DC1) / `322:322` (DC2) i `399:399`.

### Naoczny przykład: leaf strefy `priv` – `marpla-dc-1-priv-l03`

Pytamy leaf strefy **priv** o trasy MAC/IP z RT **`210:210`**, czyli VLAN-u 210 strefy **wew**.
Na tej gałęzi (bez RTC) leaf priv ma je w tablicy BGP – 12 ścieżek obcej strefy:

```
marpla-dc-1-priv-l03# show bgp evpn extcommunity rt 210:210 route-type mac-ip
          Network                Next Hop              Metric  LocPref Weight  Path
 * >Ec    RD: 10.101.1.1:210 mac-ip 001c.7331.18f2
                                 10.101.2.1            -       100     0       65100 65101 i
 * >Ec    RD: 10.101.1.1:210 mac-ip 001c.7331.18f2 10.2.10.11
                                 10.101.2.1            -       100     0       65100 65101 i
 * >Ec    RD: 10.101.1.2:210 mac-ip 001c.7331.18f2 10.2.10.11
                                 10.101.2.1            -       100     0       65100 65101 i
 * >      RD: 10.101.0.1:210 mac-ip 001c.73fa.4797 10.2.10.12
                                 10.101.3.1            -       100     0       65100 65200 65201 i
 * >      RD: 10.101.0.2:210 mac-ip 001c.73fa.4797 10.2.10.12
                                 10.101.3.2            -       100     0       65100 65200 65201 i
 (...)
```

- `RD 10.101.1.1:210` / `10.101.1.2:210`, AS path `65100 65101` – FW DC1 (`10.2.10.11`) nauczony na parze **wew**
  w DC1 (leafy `wew-l01`/`wew-l02`, VTEP 10.101.2.1), przekazany leafowi priv przez route server DC1.
- `RD 10.101.0.1:210` / `10.101.0.2:210`, AS path `65100 65200 65201` – FW DC2 (`10.2.10.12`) ze strefy **wew** DC2,
  ponownie ogłoszony przez bramy DC1.

Żadna z tych tras nie trafia do tablic routingu – leaf priv nie ma VLAN-u 210 ani VRF-u WEW, więc nie importuje
RT `210:210` ani `20:20`. Są jednak w jego **płaszczyźnie sterowania** – tak samo trasy strefy ext (`110:110`, `10:10` …).

Na gałęzi `single-domain-with-rtc` (RT Constraint) to samo zapytanie zwraca **pustą tablicę**, a cała tablica EVPN
leafa priv zawiera tylko RD/RT strefy priv (`:310`, `:321`, `:399`, `:30`) i trasy Ethernet Segment bram:

```
marpla-dc-1-priv-l03# show bgp evpn extcommunity rt 210:210 route-type mac-ip
          Network                Next Hop              Metric  LocPref Weight  Path
marpla-dc-1-priv-l03#
```


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
diagram edytowalny (fizyczny, logiczny, P2P per DC): [dual_dc/topology.drawio](dual_dc/topology.drawio).

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

Uruchomione 2026-10-06 na labie z wdrożoną konfiguracją tej gałęzi (`make deploy_cvp`, potem `make test`).

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
