from cielircours.mdtext import Mode, rendre_corps


def test_ins_devient_une_reponse_en_mode_complet():
    html = rendre_corps("Le hash fait <ins>40</ins> chiffres.", Mode.COMPLET)
    assert '<span class="reponse">40</span>' in html


def test_ins_devient_un_trou_calibre_en_mode_trous():
    html = rendre_corps("Le hash fait <ins>40</ins> chiffres.", Mode.TROUS)
    assert '<span class="trou" style="--car:2"></span>' in html
    assert "40" not in html
