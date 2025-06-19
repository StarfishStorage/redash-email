IMAGE=redash-email:latest
PATH:=/usr/lib/postgresql/16/bin:/usr/pgsql-16/bin:$(PATH)
# values used for integration test
MYIP != hostname -i
PASS != pwgen -1s 6

check:
	ruff check
	@PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=$$PYTHONPATH:src pytest tests/

format:
	ruff format
	npx prettier --write 'src/*.js'

image:
	docker build -t ${IMAGE} -f Dockerfile .

.env:
	printf "REDASH_COOKIE_SECRET=`pwgen -1s 32`\nREDASH_SECRET_KEY=`pwgen -1s 32`\n" >> .env

up: .env
	docker compose up -d
	docker compose exec server ./manage.py database create_tables
	docker compose exec server ./manage.py users create_root redash@redash.io Redash --password ${PASS}
	docker compose exec server ./manage.py ds new --type pg --options '{"dbname": "postgres", "host": "postgres", "port": 5432, "user": "postgres"}' redash
	docker compose exec postgres psql -1 -U postgres -c "SET session_replication_role = replica" -f fixtures/redash.dump > /dev/null
	@echo "maildev: http://${MYIP}:1080/"
	@echo "redash: http://${MYIP}:5001/  # redash@redash.io ${PASS}"

test:
	@tests/integration-test.sh --verbose

down:
	@touch .env
	docker compose down
	rm -f .env

dump:
	docker compose exec postgres psql -U postgres -c "UPDATE queries SET latest_query_data_id = NULL"
	docker compose exec postgres pg_dump -a -U postgres -t dashboards -t queries -t visualizations -t widgets -f fixtures/redash.dump

.PHONY: check lint image up test down dump
