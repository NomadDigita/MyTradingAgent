.PHONY: test lint run risk-go indicators-rust

test:
	python -m pytest

lint:
	python -m ruff check app tests

run:
	python -m app.main

risk-go:
	cd services/risk-go && go run .

indicators-rust:
	cd services/indicators-rust && cargo run -- --help
