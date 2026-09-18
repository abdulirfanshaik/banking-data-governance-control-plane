.PHONY: demo generate assess test clean

PYTHON ?= python3
export PYTHONPATH := src

demo: clean generate assess

generate:
	$(PYTHON) -m governance_control.generator --output data/input

assess:
	$(PYTHON) -m governance_control.engine --input data/input --output data/output --policy config/policies.json

test:
	$(PYTHON) -m unittest discover -s tests -v

clean:
	$(PYTHON) -c "from pathlib import Path; import shutil; p=Path('data/output'); [shutil.rmtree(x) if x.is_dir() else x.unlink() for x in list(p.iterdir()) if x.name != '.gitkeep']"

