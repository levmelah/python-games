# Shortcuts for building and publishing the games.
#
#   make deploy                                  # all games (slow)
#   make deploy GAME=bowling-2                   # just one, much faster
#   make deploy GAME=bowling-2 MSG="fixed score" # with your own commit message
#   make rebuild GAME=bowling-2                  # rebuild only, no push
#   make serve                                   # test locally on 127.0.0.1:8222
#
# The site: https://levmelah.github.io/python-games/

.PHONY: deploy rebuild stage build publish site serve help

GAME ?=
MSG ?=

help:
	@sed -n "2,9p" Makefile | sed "s/^#\\s\\?//"

deploy:
	sh tools/deploy.sh $(GAME) $(if $(MSG),"$(MSG)",)

rebuild:
	sh tools/rebuild.sh $(GAME)

stage:
	python3 tools/stage.py $(GAME)

build:
	ONLY=$(GAME) sh tools/build_all.sh

publish:
	python3 tools/publish.py

site:
	python3 tools/generate_site.py

serve:
	@echo "open http://127.0.0.1:8222/   --  127.0.0.1, NOT localhost!"
	cd docs && python3 -m http.server 8222
