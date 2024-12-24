.PHONY: install run clean deploy sync-secrets logs status open ssh restart certs version-* db-up db-down

# Add these database targets
db-up:
	docker-compose up -d db
	docker-compose ps
	@echo "Waiting for container to be healthy..."
	@timeout 30s bash -c 'until docker ps | grep server-db-1 | grep -q "healthy"; do sleep 1; done' || (echo "Database failed to start" && exit 1)

db-down:
	docker-compose down

# Update the run target to use Django instead of uvicorn
run: db-up wait-for-db
	python manage.py migrate
	python manage.py runserver

install:
	pip install -r requirements.txt

clean:
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete

deploy:
	fly deploy

sync-secrets:
	while IFS='=' read -r key value; do \
		if [ -n "$$key" ] && [ "$${key:0:1}" != "#" ]; then \
			fly secrets set "$$key=$$value" --app kora-server 2>/dev/null; \
		fi \
	done < .env

# Version management
version-patch:
	python scripts/bump_version.py patch

version-minor:
	python scripts/bump_version.py minor

version-major:
	python scripts/bump_version.py major

# Deploy with version bump
deploy-patch: version-patch deploy

deploy-minor: version-minor deploy

deploy-major: version-major deploy

# Fly.io commands
logs:
	fly logs --app kora-server

status:
	fly status --app kora-server

open:
	fly open --app kora-server

ssh:
	fly ssh console --app kora-server

restart: app-restart

certs:
	fly certs show --app kora-server api.materials.nyc

# Local development migrations
migrations:
	python manage.py makemigrations api

migrate:
	python manage.py migrate

# Remote migrations
remote-migrate:
	fly ssh console --app kora-server -C '/bin/sh -c "cd /app && PYTHONPATH=/app python3 manage.py migrate"'

# Database management
db-create:
	fly postgres create --name umi-db --region bos --vm-size shared-cpu-1x --volume-size 1

db-destroy:
	fly apps destroy umi-db

db-recreate: db-destroy db-create
	fly postgres attach umi-db -a kora-server

db-list:
	fly postgres list

# Database commands
db-restart:
	fly postgres restart --app umi-db
	sleep 10  # Wait for database to start

# App commands
app-start:
	fly machines start -a kora-server d8d7007f24d048

app-stop:
	fly machines stop -a kora-server d8d7007f24d048

app-restart:
	fly machines stop -a kora-server d8d7007f24d048
	sleep 5
	fly machines start -a kora-server d8d7007f24d048

db-check:
	fly ssh console --app kora-server -C 'cd /app && PYTHONPATH=/app python3 -c "import os; os.environ.setdefault(\"DJANGO_SETTINGS_MODULE\", \"core.settings\"); from django.conf import settings; from django.db import connection; print(f\"Connection usable: {connection.is_usable()}\"); connection.ensure_connection(); print(\"Connection test successful!\")"'

shell:
	fly ssh console --app kora-server

# Add this new target
wait-for-db:
	@python3 scripts/wait_for_db.py

# Show all API routes
routes:
	python manage.py show_urls | grep -v '^admin' | grep -v '^static' | column -t

# Show API routes
api-routes:
	python manage.py show_api_routes