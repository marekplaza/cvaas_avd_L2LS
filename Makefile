CURRENT_DIR := $(shell pwd)

.PHONY: help
help: ## Display help message
	@grep -E '^[0-9a-zA-Z_-]+\.*[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: start
start: ## Deploy the lab
	sudo containerlab deploy --debug --topo $(CURRENT_DIR)/clab/topology.clab.yml --max-workers 10 --timeout 5m --reconfigure

.PHONY: stop
stop: ## Destroy the lab
	sudo containerlab destroy --debug --topo $(CURRENT_DIR)/clab/topology.clab.yml --cleanup

.PHONY: inspect
inspect: ## Inspect the lab
	@sudo containerlab inspect --topo $(CURRENT_DIR)/clab/topology.clab.yml
	@echo ""
	@echo "You can check the lab status, hostnames and management addresses above."
	@echo "To connect to a lab device use \`ssh arista@<hostname>\` and password \`arista\`."

.PHONY: build
build: ## Generate AVD configs
	cd $(CURRENT_DIR)/avd_inventory; ansible-playbook playbooks/avd_build.yml

.PHONY: deploy
deploy: ## Deploy AVD configs using eAPI
	cd $(CURRENT_DIR)/avd_inventory; ansible-playbook playbooks/avd_deploy.yml

.PHONY: deploy_cvp
deploy_cvp: ## Deploy AVD configs using CloudVision
	cd $(CURRENT_DIR)/avd_inventory && \
	CVURL=$${CVURL:-www.cv-prod-euwest-2.arista.io} \
	CV_API_TOKEN=$${CV_API_TOKEN:-$$(cat $(CURRENT_DIR)/clab/cv-api-token)} \
	ansible-playbook playbooks/avd_deploy_cvp.yml

.PHONY: decommission_cvp
decommission_cvp: ## Decommission all lab devices from CVaaS inventory
	cd $(CURRENT_DIR)/avd_inventory && \
	CV_API_TOKEN=$${CV_API_TOKEN:-$$(cat $(CURRENT_DIR)/clab/cv-api-token)} \
	ansible-playbook playbooks/cvp_decommission.yml

.PHONY: diff
diff: ## Show the diff between running config and designed config
	cd $(CURRENT_DIR)/avd_inventory; ansible-playbook --diff --check playbooks/avd_deploy.yml

.PHONY: test
test: ## validate the network state
	cd $(CURRENT_DIR)/avd_inventory; ansible-playbook playbooks/avd_validate.yml
