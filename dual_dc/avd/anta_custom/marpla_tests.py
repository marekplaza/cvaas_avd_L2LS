# Custom ANTA tests for the marpla dual-DC lab.
# Loaded by the ANTA catalog as module "marpla_tests"; the Makefile adds this
# directory to PYTHONPATH for `make test` / `make test_dci`.
"""Custom EVPN tests."""

# pyright: reportAttributeAccessIssue=false
from __future__ import annotations

from typing import ClassVar

from anta.models import AntaCommand, AntaTemplate, AntaTest
from anta.tools import get_value

RT_PREFIX = "Route-Target-AS:"


class VerifyEVPNRoutesMatchImportedRT(AntaTest):
    """Verifies that the BGP EVPN table only holds routes relevant for this device.

    With BGP Route Target Constraint (RTC) a peer only receives EVPN routes that carry at
    least one route target it imports. Without RTC an eBGP route server sends every route
    and the device merely drops it at VRF import, so routes of other zones sit in its BGP table.

    Every EVPN path carrying route targets must have at least one of the given route targets.
    Paths without any route target (e.g. type-4 Ethernet Segment routes, which use the
    ES-Import community) are not evaluated.

    Expected Results
    ----------------
    * Success: Every EVPN path with route targets carries at least one expected route target.
    * Failure: At least one EVPN path carries only foreign route targets.

    Examples
    --------
    ```yaml
    marpla_tests:
      - VerifyEVPNRoutesMatchImportedRT:
          route_targets: ["30:30", "310:310", "321:321", "399:399"]
    ```
    """

    categories: ClassVar[list[str]] = ["bgp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show bgp evpn detail")]

    class Input(AntaTest.Input):
        """Input model for the VerifyEVPNRoutesMatchImportedRT test."""

        route_targets: list[str]
        """Route targets imported by this device (e.g. '30:30')."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyEVPNRoutesMatchImportedRT."""
        self.result.is_success()
        allowed = set(self.inputs.route_targets)
        foreign: list[str] = []
        checked = 0

        for route_key, route in (get_value(self.instance_commands[0].json_output, "evpnRoutes") or {}).items():
            for path in route.get("evpnRoutePaths", []):
                rts = {c[len(RT_PREFIX):] for c in path.get("routeDetail", {}).get("extCommunities", []) if c.startswith(RT_PREFIX)}
                if not rts:
                    continue
                checked += 1
                if not rts & allowed:
                    foreign.append(f"{route_key} (RT {', '.join(sorted(rts))})")

        if foreign:
            examples = "; ".join(sorted(foreign)[:5])
            self.result.is_failure(
                f"{len(foreign)} of {checked} EVPN path(s) carry only foreign route targets - e.g. {examples}"
            )
