CURRENT_DIR := $(shell pwd)
TOPO := $(CURRENT_DIR)/clab/topology.clab.yml

.PHONY: help
help: ## Display help message
	@grep -E '^[0-9a-zA-Z_-]+\.*[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: start
start: ## Deploy the dual-DC lab
	sudo containerlab deploy --debug --topo $(TOPO) --max-workers 20 --timeout 5m --reconfigure

.PHONY: stop
stop: ## Destroy the dual-DC lab
	sudo containerlab destroy --debug --topo $(TOPO) --cleanup

.PHONY: inspect
inspect: ## Inspect the dual-DC lab
	@sudo containerlab inspect --topo $(TOPO)

.PHONY: build
build: ## Generate AVD configs for DC1 and DC2
	cd $(CURRENT_DIR)/avd; ansible-playbook playbooks/avd_build.yml

.PHONY: deploy
deploy: ## Deploy AVD configs using eAPI
	cd $(CURRENT_DIR)/avd; ansible-playbook playbooks/avd_deploy.yml

.PHONY: deploy_cvp
deploy_cvp: ## Deploy AVD configs using CloudVision
	cd $(CURRENT_DIR)/avd && \
	CVURL=$${CVURL:-www.cv-prod-euwest-2.arista.io} \
	CV_API_TOKEN=$${CV_API_TOKEN:-$$(cat $(CURRENT_DIR)/../clab/cv-api-token)} \
	ansible-playbook playbooks/avd_deploy_cvp.yml

.PHONY: diff
diff: ## Show the diff between running config and designed config
	cd $(CURRENT_DIR)/avd; ansible-playbook --diff --check playbooks/avd_deploy.yml

.PHONY: test
test: ## Validate the network state with ANTA
	cd $(CURRENT_DIR)/avd; ansible-playbook playbooks/avd_validate.yml

.PHONY: fw_test
fw_test: ## Ping anycast GWs and the remote FW node across the DCI from both FW nodes
	@for fw in marpla-dc-1-fw01 marpla-dc-2-fw01; do echo "== $$fw"; docker exec $$fw Cli -p 15 -c "test"; done
