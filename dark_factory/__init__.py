"""Repository-local import shim for `python -m dark_factory`.

Installed targets use `.agents/lib/dark_factory`; this shim only makes the
source checkout runnable without setting `PYTHONPATH`.
"""

from pathlib import Path

__path__.append(str(Path(__file__).resolve().parents[1] / "tools" / "dark_factory"))
__version__ = "0.1.0"
