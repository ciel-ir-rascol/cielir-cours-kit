from datetime import date
from pathlib import Path

import pytest

from cielircours.config import Cours, lire_config
from cielircours.rendu import Publication

DONNEES = Path(__file__).parent / "data"


@pytest.fixture
def cours() -> Cours:
    return lire_config(DONNEES / "cours-cpp.yml")


@pytest.fixture
def pub() -> Publication:
    return Publication("v1.02", date(2026, 10, 29))
