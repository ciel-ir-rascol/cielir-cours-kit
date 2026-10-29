"""Le tag d'un dépôt de cours : vX.YY, rien d'autre. L'action le contrôle avant tout."""

import pytest

from cielircours.cli import TAG_VALIDE


@pytest.mark.parametrize("tag", ["v1.2", "1.01", "v1.01-rc", "v1.012", "v1.01\n", "", "v.01", "xv1.01", "v\u0661.\u0660\u0661"])
def test_un_tag_malforme_est_refuse(tag):
    assert not TAG_VALIDE.match(tag)


@pytest.mark.parametrize("tag", ["v1.01", "v12.03", "v0.99"])
def test_un_tag_conforme_est_accepte(tag):
    assert TAG_VALIDE.match(tag)
