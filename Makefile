.PHONY: setup test lint build up down logs

setup:            ## create data dirs writable by the container user (uid 10001)
	mkdir -p data/inbox data/outbox models
	sudo chown 10001:10001 data/outbox

test:
	python -m pytest -q

lint:
	ruff check . && ruff format --check .

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f
