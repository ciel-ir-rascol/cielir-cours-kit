# Cibles locales du kit : tout passe par `uv run` ou Docker (hyperion n'a ni Node ni LaTeX).
#
#   make test      les tests du kit
#   make temoin    régénère le dépôt témoin : contrôle, cours.pdf, cours-a-trous.pdf, slides.pdf, site
#   make slides    le deck seul (Marp dans Docker)
#   make site      le site tel que GitHub Pages le publie : accueil, fiche et slides, dans build/…/site/
#   make servir    sert ce site sur 0.0.0.0:8000 (hyperion est sans écran : ouvrir l'adresse Tailscale)
#   make clean     supprime build/
#
# Le témoin est le cours jouet qui exerce toute la mise en page. Le tag v1 du kit ne bouge
# que s'il se régénère sans régression : relire les trois PDF à l'œil, en couleur puis en
# niveaux de gris. Version et date du témoin sont fixes pour qu'on puisse le comparer d'une
# génération à l'autre ; elles ne sont jamais écrites dans ses sources.
#
# Les fichiers générés vont dans build/ (ignoré par git), jamais dans le dépôt de cours.

DEPOT      ?= temoin
VERSION    ?= v1.01
DATE       ?= 2026-10-29
BUILD      ?= build/$(notdir $(DEPOT))
PORT       ?= 8000
DECK       ?= $(firstword $(wildcard $(DEPOT)/slides/[0-9][0-9]-*.md))

# Marp CLI épinglé : une mise à jour se décide, elle ne se subit pas.
MARP_IMAGE := marpteam/marp-cli:v4.5.1
CLI        := uv run cielir-cours

.PHONY: temoin test verifier pdf slides site servir clean

temoin: verifier pdf slides site
	@echo "Témoin régénéré dans $(BUILD)/ :" && ls -1 $(BUILD)/*.pdf

test:
	uv run pytest

verifier:
	$(CLI) verifier $(DEPOT)

pdf:
	mkdir -p $(BUILD)
	$(CLI) pdf $(DEPOT)/COURS.md --config $(DEPOT)/cours.yml --mode complet \
	    --version $(VERSION) --date $(DATE) -o $(BUILD)/cours.pdf
	$(CLI) pdf $(DEPOT)/COURS.md --config $(DEPOT)/cours.yml --mode trous \
	    --version $(VERSION) --date $(DATE) -o $(BUILD)/cours-a-trous.pdf

# La copie du deck (avec la version) est écrite à côté d'une copie de img/, pour que les
# images relatives se résolvent ; Marp est lancé en tant qu'utilisateur courant.
slides:
	mkdir -p $(BUILD)/deck
	$(CLI) deck $(DECK) --config $(DEPOT)/cours.yml --version $(VERSION) --date $(DATE) -o $(BUILD)/deck/$(notdir $(DECK))
	rm -rf $(BUILD)/deck/img && cp -R $(DEPOT)/slides/img $(BUILD)/deck/img
	docker run --rm --init \
	    -e MARP_USER="$$(id -u):$$(id -g)" -e CHROME_NO_SANDBOX=1 \
	    -v "$(CURDIR):/work" -w /work \
	    $(MARP_IMAGE) \
	    --theme-set themes/ciel.css --allow-local-files --html --pdf \
	    $(BUILD)/deck/$(notdir $(DECK)) -o $(BUILD)/slides.pdf

# Le site, comme l'action le publie : l'accueil et la fiche viennent du kit, le diaporama de Marp
# (HTML, sous slides/). La copie du deck écrite par `make slides` sert aussi ici.
site: slides
	rm -rf $(BUILD)/site
	$(CLI) site $(DEPOT)/COURS.md --config $(DEPOT)/cours.yml \
	    --version $(VERSION) --date $(DATE) -o $(BUILD)/site
	docker run --rm --init \
	    -e MARP_USER="$$(id -u):$$(id -g)" -e CHROME_NO_SANDBOX=1 \
	    -v "$(CURDIR):/work" -w /work \
	    $(MARP_IMAGE) \
	    --theme-set themes/ciel.css --allow-local-files --html \
	    $(BUILD)/deck/$(notdir $(DECK)) -o $(BUILD)/site/slides/index.html
	cp -R $(BUILD)/deck/img $(BUILD)/site/slides/img
	@echo "Site écrit dans $(BUILD)/site/"

servir: site
	@echo "http://100.88.2.20:$(PORT)/  (Tailscale)"
	cd $(BUILD)/site && python3 -m http.server $(PORT) --bind 0.0.0.0

clean:
	rm -rf build
