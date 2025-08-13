venv:
	python3 -m venv backend/.venv

install:
	backend/.venv/bin/pip install -r backend/requirements.txt

run:
	backend/.venv/bin/python -m app.main

test:
	backend/.venv/bin/pytest -q

compose-up:
	docker compose up -d postgres redis backend

compose-down:
	docker compose down