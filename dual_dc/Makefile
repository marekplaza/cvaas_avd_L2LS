CURRENT_DIR := $(shell pwd)
TOPO := $(CURRENT_DIR)/clab/topology.clab.yml
# custom ANTA tests (marpla_tests) used by the DCI catalog
ANTA_ENV := PYTHONPATH=$(CURRENT_DIR)/avd/anta_custom$${PYTHONPATH:+:$$PYTHONPATH}

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
build: ## Generate AVD configs for DC1 and DC2 and the DCI test catalog
	cd $(CURRENT_DIR)/avd; ansible-playbook playbooks/avd_build.yml
	cd $(CURRENT_DIR)/avd; python3 gen_dci_catalog.py

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
test: ## fw_test (generates traffic for type-2 checks) + ANTA: AVD catalogs and BGP/EVPN/DCI tests
	-$(CURRENT_DIR)/fw_test.sh
	cd $(CURRENT_DIR)/avd; $(ANTA_ENV) ansible-playbook playbooks/avd_validate.yml

.PHONY: test_dci
test_dci: ## fw_test + only the BGP/EVPN/DCI tests (avd/anta_catalogs/dci_tests.yml)
	-$(CURRENT_DIR)/fw_test.sh
	cd $(CURRENT_DIR)/avd; $(ANTA_ENV) ansible-playbook playbooks/avd_validate.yml -e avd_catalogs_enabled=false

.PHONY: fw_test
fw_test: ## Data-plane test from both FW nodes: anycast GWs, stretched VLANs and HA VLAN across DCI
	$(CURRENT_DIR)/fw_test.sh
