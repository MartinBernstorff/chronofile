###########################
# Start template makefile #
###########################

SRC_PATH = chronofile
MAKEFLAGS = --no-print-directory

# Dependency management
install:
	uv sync

quicksync:
	uv sync --frozen

test:
	@pytest .

lint: ## Format code
	@echo "––– Linting –––"
	@uv run ruff format .
	@uv run ruff . --fix --unsafe-fixes
	@echo "✅✅✅ Lint ✅✅✅"

types: ## Type-check code
	@echo "––– Type-checking –––"
	@uv run pyright .
	@echo "✅✅✅ Types ✅✅✅"

validate_ci: ## Run all checks
	@echo "––– Running all checks –––"
	@make lint
	@make types
	## CI doesn't support local coverage report, so skipping full test
	@make test

docker_ci: ## Run all checks in docker
	@echo "––– Running all checks in docker –––"
	docker build -t chronofile_ci  -f .github/Dockerfile.dev .
	docker run --env-file .env chronofile_ci make validate_ci

#########################
# End template makefile #
#########################

docker_build:
	docker build -t ghcr.io/martinbernstorff/chronofile:latest .

docker_deploy: docker_build
	docker compose up -d

docker_smoketest: docker_build
	docker compose run app --dry-run