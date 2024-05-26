###########################
# Start template makefile #
###########################

SRC_PATH = rescuetime2gcal
MAKEFLAGS = --no-print-directory

# Dependency management
install:
	rye sync

quicksync:
	rye sync --no-lock

test:
	@rye test

test-with-coverage: 
	@echo "––– Testing –––"
	@make test
	@rye run diff-cover .coverage.xml
	@echo "✅✅✅ Tests passed ✅✅✅"

lint: ## Format code
	@echo "––– Linting –––"
	@rye run ruff format .
	@rye run ruff . --fix --unsafe-fixes \
		--extend-select F401 \
		--extend-select F841
	@echo "✅✅✅ Lint ✅✅✅"

types: ## Type-check code
	@echo "––– Type-checking –––"
	@rye run pyright .
	@echo "✅✅✅ Types ✅✅✅"

validate_ci: ## Run all checks
	@echo "––– Running all checks –––"
	@make lint
	@make types
	## CI doesn't support local coverage report, so skipping full test
	@make test

docker_ci: ## Run all checks in docker
	@echo "––– Running all checks in docker –––"
	docker build -t rescuetime2gcal_ci  -f .github/Dockerfile.dev .
	docker run --env-file .env rescuetime2gcal_ci make validate_ci

pr: ## Submit a PR
	@lumberman sync --squash --automerge

#########################
# End template makefile #
#########################

docker_build:
	docker build -t rescuetime-to-gcal:latest .

docker_deploy: docker_build
	docker run --env-file .env --network host rescuetime-to-gcal:latest r2s sync

docker_smoketest: docker_build
	docker run --env-file .env --network host rescuetime-to-gcal:latest r2s sync --dry-run 