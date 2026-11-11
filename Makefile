IMAGE := kgb-zi-map-tools:alpha11
RUN := docker run --rm --platform linux/amd64 --network none -v "$(CURDIR):/work" $(IMAGE)
.PHONY: generate toolchain compile validate test package repro preview

generate:
	python3 tools/generate.py

toolchain:
	sh tools/bootstrap.sh

compile:
	$(RUN) sh tools/compile.sh build/candidate

validate:
	python3 tools/validate.py > evidence/qualification.json

test:
	python3 -m unittest discover -s tests -v

package:
	python3 tools/package.py

repro:
	$(RUN) sh tools/compile.sh build/repro
	python3 tools/check_repro.py

preview:
	$(RUN) sh tools/preview.sh
