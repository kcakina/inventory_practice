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

reserve:
	curl -s -X POST http://localhost:8080/reserve \
		-H "Content-Type: application/json" \
		-d '{"sku": "widget", "user_id": "user1", "qty": 5}' | python3 -m json.tool

reserve-too-many:
	curl -s -X POST http://localhost:8080/reserve \
		-H "Content-Type: application/json" \
		-d '{"sku": "widget", "user_id": "user1", "qty": 999}' | python3 -m json.tool

reserve-bad-sku:
	curl -s -X POST http://localhost:8080/reserve \
		-H "Content-Type: application/json" \
		-d '{"sku": "nonexistent", "user_id": "user1", "qty": 1}' | python3 -m json.tool

reserve-bad-qty:
	curl -s -X POST http://localhost:8080/reserve \
		-H "Content-Type: application/json" \
		-d '{"sku": "widget", "user_id": "user1", "qty": 0}' | python3 -m json.tool

.PHONY: test
test:
	.venv/bin/pytest test/