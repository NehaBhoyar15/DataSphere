"""Recovery loader for the original InsightIQ dashboard."""

from importlib.machinery import SourcelessFileLoader
from importlib.util import spec_from_loader, module_from_spec
from pathlib import Path

_recovery_path = (
    Path(__file__).resolve().parent / "dashboard_recovery.pyc"
)

if not _recovery_path.exists():
    raise FileNotFoundError(
        f"Dashboard recovery file not found: {_recovery_path}"
    )

_loader = SourcelessFileLoader(
    "ui._dashboard_recovered",
    str(_recovery_path),
)

_spec = spec_from_loader(_loader.name, _loader)

if _spec is None:
    raise ImportError("Could not create dashboard recovery loader.")

_module = module_from_spec(_spec)
_loader.exec_module(_module)

DashboardPage = _module.DashboardPage
Dashboard = getattr(_module, "Dashboard", DashboardPage)
ExecutiveDashboard = getattr(
    _module, "ExecutiveDashboard", DashboardPage
)
