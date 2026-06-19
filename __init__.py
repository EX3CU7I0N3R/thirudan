"""SRM Academia scraper modules."""

from pathlib import Path
import sys

module_dir = str(Path(__file__).resolve().parent)
if module_dir not in sys.path:
    sys.path.insert(0, module_dir)

from scraper.workflow import AcademiaScraper

__all__ = ["AcademiaScraper"]
