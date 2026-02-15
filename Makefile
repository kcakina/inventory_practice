venv:
	python3 -m venv .venv

activate:
	source .venv/bin/activate

install:
	.venv/bin/pip install -r requirements.txt

run:
	.venv/bin/python main.py

test-endpoint:
	curl http://localhost:8080/

.PHONY: test
test:
	.venv/bin/pytest test/