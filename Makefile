IMAGE=redash-email:latest
PATH:=/usr/lib/postgresql/16/bin:/usr/pgsql-16/bin:$(PATH)
# values used for integration test
MYIP != tests/myip.sh
PASS != tests/pwgen.py 8

image:
	docker build -t ${IMAGE} -f Dockerfile .

format:
	ruff format
	npx prettier --write 'src/*.js'

tests:
	ruff check
	@PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=$$PYTHONPATH:src pytest tests/

.env:
	printf "REDASH_COOKIE_SECRET=`tests/pwgen.py 32`\nREDASH_SECRET_KEY=`tests/pwgen.py 32`\n" >> .env

up: .env
	docker compose up --quiet-pull -d
	docker compose exec server ./manage.py database create_tables
	docker compose exec server ./manage.py users create_root redash@redash.io Redash --password ${PASS}
	docker compose exec server ./manage.py ds new --type pg --options '{"dbname": "postgres", "host": "postgres", "port": 5432, "user": "postgres"}' redash
	docker compose exec postgres psql -1 -U postgres -c "SET session_replication_role = replica" -f fixtures/redash.dump > /dev/null
	@echo "maildev: http://${MYIP}:1080/"
	@echo "redash: http://${MYIP}:5001/  # redash@redash.io ${PASS}"

integration-tests:
	tests/integration-test.sh --verbose

down:
	@touch .env
	docker compose down
	rm -f .env

dump:
	docker compose exec postgres psql -U postgres -c "UPDATE queries SET latest_query_data_id = NULL"
	docker compose exec postgres pg_dump -a -U postgres -t dashboards -t queries -t visualizations -t widgets -f fixtures/redash.dump

.PHONY: image format tests up integration-test down dump
