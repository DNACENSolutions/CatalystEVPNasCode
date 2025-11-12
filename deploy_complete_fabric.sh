#!/bin/bash

# Complete EVPN Fabric Deployment with Catalyst Center Integration
# This script demonstrates end-to-end deployment using both EVPN-specific 
# and Catalyst Center validated workflows

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "ansible.cfg" ] || [ ! -d "catalyst-center-iac" ]; then
    print_error "Please run this script from the CatalystEVPNasCode root directory"
    print_error "Make sure the catalyst-center-iac submodule is initialized"
    exit 1
fi

# Configuration
INVENTORY_FILE="inventory/hosts.yml"
CATALYST_CENTER_WORKFLOWS="catalyst-center-iac/workflows"
EVPN_PLAYBOOKS="playbooks"

print_status "Starting Complete EVPN Fabric Deployment"
print_status "========================================"

# Phase 1: Foundation Setup (Day 0)
print_status "Phase 1: Foundation Setup (Day 0)"
print_status "---------------------------------"

# 1.1 Site Hierarchy
print_status "1.1 Setting up site hierarchy..."
cd "${CATALYST_CENTER_WORKFLOWS}/site_hierarchy"
if [ -f "vars/site_hierarchy_vars.yml" ]; then
    ansible-playbook playbook/site_hierarchy_playbook.yml -i "../../${INVENTORY_FILE}"
    print_success "Site hierarchy configured"
else
    print_warning "Site hierarchy vars not found, skipping..."
fi
cd - > /dev/null

# 1.2 Network Settings
print_status "1.2 Configuring global network settings..."
cd "${CATALYST_CENTER_WORKFLOWS}/network_settings"
if [ -f "vars/network_settings_vars.yml" ]; then
    ansible-playbook playbook/network_settings_playbook.yml -i "../../${INVENTORY_FILE}"
    print_success "Network settings configured"
else
    print_warning "Network settings vars not found, skipping..."
fi
cd - > /dev/null

# 1.3 Device Credentials
print_status "1.3 Setting up device credentials..."
cd "${CATALYST_CENTER_WORKFLOWS}/device_credentials"
if [ -f "vars/device_credentials_vars.yml" ]; then
    ansible-playbook playbook/device_credentials_playbook.yml -i "../../${INVENTORY_FILE}"
    print_success "Device credentials configured"
else
    print_warning "Device credentials vars not found, skipping..."
fi
cd - > /dev/null

# Phase 2: Device Management (Day 1)
print_status "Phase 2: Device Management (Day 1)"
print_status "----------------------------------"

# 2.1 Device Discovery
print_status "2.1 Discovering devices..."
cd "${CATALYST_CENTER_WORKFLOWS}/device_discovery"
if [ -f "vars/device_discovery_vars.yml" ]; then
    ansible-playbook playbook/device_discovery_playbook.yml -i "../../${INVENTORY_FILE}"
    print_success "Device discovery completed"
else
    print_warning "Device discovery vars not found, skipping..."
fi
cd - > /dev/null

# 2.2 Device Templates
print_status "2.2 Configuring device templates..."
cd "${CATALYST_CENTER_WORKFLOWS}/device_templates"
if [ -f "vars/device_templates_vars.yml" ]; then
    ansible-playbook playbook/device_templates_playbook.yml -i "../../${INVENTORY_FILE}"
    print_success "Device templates configured"
else
    print_warning "Device templates vars not found, skipping..."
fi
cd - > /dev/null

# 2.3 Device Provisioning
print_status "2.3 Provisioning devices..."
cd "${CATALYST_CENTER_WORKFLOWS}/provision"
if [ -f "vars/provision_vars.yml" ]; then
    ansible-playbook playbook/provision_playbook.yml -i "../../${INVENTORY_FILE}"
    print_success "Device provisioning completed"
else
    print_warning "Provision vars not found, skipping..."
fi
cd - > /dev/null

# Phase 3: EVPN Fabric Deployment (Core)
print_status "Phase 3: EVPN Fabric Deployment (Core)"
print_status "--------------------------------------"

# 3.1 EVPN Deployment
print_status "3.1 Deploying EVPN fabric..."
cd "${EVPN_PLAYBOOKS}"
if [ -f "evpn_deployment.yml" ]; then
    ansible-playbook evpn_deployment.yml -i "../${INVENTORY_FILE}"
    print_success "EVPN fabric deployed"
else
    print_error "EVPN deployment playbook not found!"
    exit 1
fi
cd - > /dev/null

# Phase 4: SDA Fabric Configuration (Day 2)
print_status "Phase 4: SDA Fabric Configuration (Day 2)"
print_status "-----------------------------------------"

# 4.1 SDA Fabric Sites and Zones
print_status "4.1 Configuring SDA fabric sites and zones..."
cd "${CATALYST_CENTER_WORKFLOWS}/sda_fabric_sites_zones"
if [ -f "vars/sda_fabric_sites_zones_vars.yml" ]; then
    ansible-playbook playbook/sda_fabric_sites_zones_playbook.yml -i "../../${INVENTORY_FILE}"
    print_success "SDA fabric sites and zones configured"
else
    print_warning "SDA fabric sites vars not found, skipping..."
fi
cd - > /dev/null

# 4.2 SDA Virtual Networks and Gateways
print_status "4.2 Configuring SDA virtual networks and L2/L3 gateways..."
cd "${CATALYST_CENTER_WORKFLOWS}/sda_virtual_networks_l2l3_gateways"
if [ -f "vars/sda_virtual_networks_l2l3_gateways_vars.yml" ]; then
    ansible-playbook playbook/sda_virtual_networks_l2l3_gateways_playbook.yml -i "../../${INVENTORY_FILE}"
    print_success "SDA virtual networks and gateways configured"
else
    print_warning "SDA virtual networks vars not found, skipping..."
fi
cd - > /dev/null

# 4.3 SDA Host Onboarding
print_status "4.3 Configuring SDA host onboarding policies..."
cd "${CATALYST_CENTER_WORKFLOWS}/sda_hostonboarding"
if [ -f "vars/sda_hostonboarding_vars.yml" ]; then
    ansible-playbook playbook/sda_hostonboarding_playbook.yml -i "../../${INVENTORY_FILE}"
    print_success "SDA host onboarding configured"
else
    print_warning "SDA host onboarding vars not found, skipping..."
fi
cd - > /dev/null

# Phase 5: Integration and Security (Optional)
print_status "Phase 5: Integration and Security (Optional)"
print_status "-------------------------------------------"

# 5.1 ISE Integration
print_status "5.1 Configuring ISE integration..."
cd "${CATALYST_CENTER_WORKFLOWS}/ise_radius_integration"
if [ -f "vars/ise_radius_integration_vars.yml" ]; then
    ansible-playbook playbook/ise_radius_integration_playbook.yml -i "../../${INVENTORY_FILE}"
    print_success "ISE integration configured"
else
    print_warning "ISE integration vars not found, skipping..."
fi
cd - > /dev/null

# Final Status
print_success "========================================"
print_success "Complete EVPN Fabric Deployment Finished!"
print_success "========================================"

print_status "Deployment Summary:"
print_status "- Foundation setup (Day 0): Site hierarchy, network settings, credentials"
print_status "- Device management (Day 1): Discovery, templates, provisioning"
print_status "- EVPN fabric deployment: Core BGP EVPN-VXLAN fabric"
print_status "- SDA configuration (Day 2): Fabric sites, virtual networks, host policies"
print_status "- Security integration: ISE/RADIUS integration"

print_status ""
print_status "Next steps:"
print_status "1. Verify fabric status in Catalyst Center GUI"
print_status "2. Test connectivity between sites"
print_status "3. Validate policy enforcement"
print_status "4. Monitor fabric health and performance"

print_success "Deployment completed successfully!"
