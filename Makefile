.PHONY: load ratios test report dashboard api clean

load:
	python -m src.etl.loader

ratios:
	python -m src.etl.loader --ratios

test:
	pytest tests/etl -v

report:
	python -m src.etl.validator

dashboard:
	@echo "Dashboard target reserved for later module."

api:
	@echo "API target reserved for later module."

clean:
	@echo "Clean target."