# Notatki z sesji – 2026-10-05/06

Co zostało zrobione, dlaczego tak, na jakie pułapki trafiliśmy i od czego zacząć, jeśli chcesz pracować dalej.
Ten sam plik jest na gałęziach `dualDCandDCI`, `single-domain`, `single-domain-with-rtc` i `multi-domain`.

## Gałęzie

| Gałąź | Stan | Główna różnica |
|---|---|---|
| `main` | lab jednego DC (L2LS) + CVaaS | punkt wyjścia, bez labu dual DC |
| `dualDCandDCI` | dual DC bez RTC + pełna dokumentacja draw.io | gałąź rozwojowa, z niej wyrosły warianty |
| `single-domain` | wspólne bramy EVPN na spine'ach, bez RTC | strefy rozdzielone tylko VRF/RT; trasy EVPN wszystkich stref w tablicach leafów |
| `single-domain-with-rtc` | jak wyżej + RT Constraint | leaf dostaje tylko trasy swojej strefy; strefy spotykają się na spine'ach (bramach) |
| `multi-domain` | bramy per strefa na parach leafów, spine'y = route servery | osobne domeny EVPN, osobne sesje i tunele DCI per strefa |

Każda gałąź ma własne `README.md` (konfiguracja, wyniki testów z labu, schematy PNG). Lab w chwili zamknięcia
sesji ma wdrożoną konfigurację `multi-domain`.

## Co zrobiliśmy – chronologicznie

### Lab jednego DC (`main`)
1. **Aktualizacja do AVD 6.4 / pyavd 6.4** (z 5.2), `arista.eos` 12.3, `ansible-core` 2.17.14 (maks. dla Pythona 3.10).
   Migracja kluczy: `local_users` → `aaa_settings.local_users`, `mgmt_interface` → `mgmt_interface_settings.interface`,
   DNS przez natywne `dns_settings`, `management_eapi.enabled: true`.
2. **Token CVaaS w containerlabie**: `extras.ceos-copy-to-flash` w `defaults` nie działał w clab 0.76 – zamiana na bind w `kinds.ceos`.
3. **`make test`**: `eos_validate_state` usunięte w AVD 6 → `anta_runner`.
4. **CVaaS**: hierarchia sieci przez `dc_name`/`pod_name` (tagi `topology_hint_*`), tag `owner:marpla`,
   prefiks nazw `marpla-` (podkreślnik w hostname EOS jest niepoprawny), unikalne numery seryjne `CAFECAFECAFE00xx`.
5. **Obraz cEOS**: `get_ceos.sh` (curl) zamiast `ardl` – arista.com odpowiada klientom Pythona stroną „Client Challenge”.
   Lab przeniesiony na `arista/ceos:4.35.6M`, stare obrazy usunięte.

### Lab dual DC (`dual_dc/`)
6. **Projekt**: 2 DC × (2 spine'y + 3 pary MLAG leafów: `wew`, `priv`, `ext`), DCI 4 × /31 spine ↔ spine,
   eBGP underlay + eBGP EVPN, ASN DC1 651xx / DC2 652xx, każda para własny ASN, L2VNI ext 100xxxx / wew 200xxxx /
   priv 300xxxx, ten sam anycast GW w obu DC, geo-rozciągnięty klaster FW A/P (cEOS jako host, `fw_test.sh`).
   Każdy DC to osobny fabric AVD (dwa play'e w `avd_build.yml`).
7. **Wariant single-domain**: spine'y jako VTEP + brama EVPN multi-domain (własny typ węzła), all-active multihoming
   (I-ESI) + D-path, DCI przepuszcza tylko loopbacki bram, filtr `RM-UNDERLAY-TO-LEAFS`, przez DCI tylko VNI z tagiem `dci`.
8. **Testy**: `gen_dci_catalog.py` generuje katalog ANTA z `structured_configs` (sesje, VTEP-y, VNI, type-2/5,
   route-mapy DCI); `make test` / `make test_dci` uruchamia `fw_test` + ANTA.
9. **Dokumentacja**: `topology.drawio` (fizyczna, logiczna, P2P per DC, RD i RT) z `tools/gen_drawio.py`,
   PNG do README z `tools/gen_png.py` (matplotlib).
10. **RT Constraint** (`single-domain-with-rtc`): `evpn_overlay_bgp_rtc: true` + własny test
    `VerifyEVPNRoutesMatchImportedRT` (`avd/anta_custom/marpla_tests.py`). Leaf priv: 144 → 40 ścieżek EVPN.
11. **`make deploy_cvp`** zatwierdza i uruchamia change control automatycznie (`cv_run_change_control: true`).
12. **Multi-domain** (wariant A): bramą każdej strefy jest jej para leafów (`evpn_gateway` na `node_group`),
    spine'y wracają do domyślnego typu (route server bez VTEP), sesje `EVPN-OVERLAY-CORE` para ↔ para,
    VLAN-y lokalne `evpn_l2_multi_domain: false`, poprawka RTC (`RM-RTC-LOCAL-ONLY`).

## Pułapki i lekcje

| Problem | Objaw | Rozwiązanie |
|---|---|---|
| AVD 6 po cichu pomija usunięte klucze w `custom_structured_configuration_*` | build bez błędów, a w configu brak DNS / eAPI | po każdej aktualizacji AVD porównać `intended/configs`, nie ufać samemu buildowi |
| `NETWORK_PROVISIONING_DISABLED` na tenancie | `make decommission_cvp` (`cv_device_v3`, stare API) nie działa | decommission przez Resource API `inventory/v1/DeviceDecommissioningConfig` albo GUI |
| decommission przy wyłączonym TerminAttr | status „Trying to disable TerminAttr on device” w nieskończoność | lab i TerminAttr muszą działać do końca decommission, dopiero potem `make stop` |
| `_` w hostname | EOS: „not a valid Internet hostname”, hostname nieustawiony | prefiks `marpla-` |
| `ardl` | `JSONDecodeError` – arista.com „Client Challenge” dla Pythona | `get_ceos.sh` (curl) |
| `VerifyBGPPeerSession` po deployu | chwilowe `OutQ` > 0 przy dużym obciążeniu labu | `check_tcp_queues: false` |
| `VerifyBGPExchangedRoutes` przez DCI | trasa odebrana z obu łączy, „Active: False” na jednym (ECMP) | `check_active: false` |
| RTC w multi-domain | członkostwo `0/0` route serverów przechodzi przez bramę i DCI → leafy dostają trasy wszystkich stref; wyłączenie RTC na core pogarsza (peer bez RTC wymusza własne `0/0`) | `RM-RTC-LOCAL-ONLY` (as-path `^$`) out w `rt-membership` przez `raw_eos_cli` |
| D-path na bramach MLAG | AVD go nie generuje | w AVD tylko z all-active multihoming (niedostępne z MLAG); w tym układzie pętlę blokuje AS path pary |
| `git add -A dual_dc` | do commita trafia `topology.clab.yml.annotations.json` (rozszerzenie clab w VS Code) | dodawać pliki jawnie albo dopisać `*.annotations.json` do `.gitignore` |

## Jak pracować dalej

```bash
cd dual_dc
make start          # lab (sudo; containerlab 0.76 działa też bez sudo dla grupy clab_admins)
make build          # AVD + katalog testów
make deploy_cvp     # CVaaS z automatycznym change control (albo make deploy – eAPI)
make test_dci       # fw_test + testy BGP/EVPN/DCI/RTC; pełny: make test
```

- Przełączenie labu na inną gałąź: `git switch <gałąź>` → `cd dual_dc && make deploy_cvp` (konfiguracja jest w `intended/`).
- Po zmianie adresacji / topologii: `make build`, potem `python3 tools/gen_drawio.py` i
  `python3 tools/gen_png.py` (PNG wymaga matplotlib – najprościej w venv).
- Raporty ANTA: `dual_dc/avd/anta/reports/` (poza repo).
- Commity robi Claude, push – właściciel repo.

## Otwarte tematy / pomysły na dalej

1. **Route servery per strefa** – w `multi-domain` spine'y nadal znają trasy wszystkich stref własnego DC (bez importu).
   Pełna separacja: leafy bez route serverów (przy jednej parze na strefę nie są potrzebne) albo osobne RS per strefa.
2. **Wariant B** – dedykowane border leafy jako bramy per strefa (gdy w strefie będzie więcej par leafów).
3. **Wariant C** – osobny underlay DCI per strefa (podinterfejsy + VRF-lite na łączach DCI).
4. **Filtr underlay per strefa** – dziś przez DCI idą loopbacki leafów wszystkich stref; można zawęzić do pary tej samej strefy.
5. **`make decommission_cvp`** – przepisać na Resource API (`DeviceDecommissioningConfig`) zamiast `cv_device_v3`.
6. **Sprzątanie CVaaS** – stare configlety `AVD-*` / `INIT-*` i wpisy Inventory & Topology po poprzednich wersjach labu.
7. **`.gitignore`** – `*.annotations.json`; plik `dodatek` (rozszerzenie `monitor_connectivity`) nadal poza repo.
8. **Testy** – test negatywny „brak loopbacków innych stref w underlay leafa”, sprawdzenie, że route servery nie mają VRF/VXLAN.
