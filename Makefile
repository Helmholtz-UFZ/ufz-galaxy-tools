INSTANCE ?= galaxy.ufz.de

## The yml files grow with the number of installed tools, so the targets below run in parallel.
NPROC := $(shell nproc 2>/dev/null || sysctl -n hw.logicalcpu) ## Workaround since MacOS does not have nproc

SECTIONS := find ./$(INSTANCE)/sections/ -name '*.yml' | grep '^\./[^/]*/'
LOCKFILES := find ./$(INSTANCE)/sections/ -name '*.yml.lock' | grep '^\./[^/]*/'

help: ## Show this help
	@egrep '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-16s\033[0m %s\n", $$1, $$2}'

lint: ## Lint all yaml files for the given INSTANCE
	# Check the yml files have valid syntax and are loadable
	$(SECTIONS) | xargs -n 1 -P $(NPROC) python3 scripts/yaml_check.py
	# Validate the yml files against the schema
	$(SECTIONS) | xargs -n 1 -P $(NPROC) -I {} pykwalify -d '{}' -s ./$(INSTANCE)/schema/.schema.yml
	# Verify that all repositories have at least one revision
	$(SECTIONS) | xargs -n 1 -P $(NPROC) python3 scripts/identify_unpinned.py

fix: ## For the given INSTANCE fix all lockfiles and add the latest revision to every repo that has no revision
	# Generate the lockfile or update it if it is missing tools. Also add flags for dependency handling.
	$(SECTIONS) | xargs -n 1 -P $(NPROC) python3 scripts/fix_lockfile.py
	# Add the latest revision to every repository that has no revision
	$(SECTIONS) | xargs -n 1 -P $(NPROC) python3 scripts/update_tool.py --without --log debug

update-owner: ## For the given INSTANCE update all tools that are owned by REPO_OWNER
	$(SECTIONS) | xargs -n 1 -P $(NPROC) python3 scripts/update_tool.py --owner $(REPO_OWNER)

update-repo: ## For the given INSTANCE update the tool REPO_NAME
	$(SECTIONS) | xargs -n 1 -P $(NPROC) python3 scripts/update_tool.py --name $(REPO_NAME)

update-all: ## For the given INSTANCE update all tools
	$(SECTIONS) | xargs -n 1 -P $(NPROC) python3 scripts/update_tool.py

fix-outdated: ## Replace non-installable revisions in the lockfiles (needs hg + galaxy-tool-util, slow)
	$(LOCKFILES) | xargs -n 1 -P 1 python3 scripts/fix_outdated.py

install: ## For the given INSTANCE install all revisions that are missing
	$(LOCKFILES) | xargs -n 1 -P 1 -I {} shed-tools install --toolsfile {} --galaxy $(INSTANCE) --api_key $(GALAXY_API_KEY) --skip_install_resolver_dependencies

.PHONY: help lint fix update-owner update-repo update-all fix-outdated install
