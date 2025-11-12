# Catalyst Center Ansible IaC Integration

This project now includes the comprehensive Catalyst Center Ansible IaC workflows as a Git submodule, providing access to 30+ validated playbooks for complete network automation.

## 📁 Repository Structure

```
CatalystEVPNasCode/
├── catalyst-center-iac/          # Git submodule with 30+ workflows
│   └── workflows/
│       ├── site_hierarchy/       # Site management
│       ├── device_discovery/     # Device onboarding
│       ├── provision/           # Device provisioning
│       ├── sda_fabric_sites_zones/ # SDA fabric management
│       ├── network_settings/    # Global network settings
│       ├── device_templates/    # Configuration templates
│       ├── ise_radius_integration/ # ISE integration
│       └── ... (25+ more workflows)
├── playbooks/                   # Project-specific EVPN playbooks
├── data/                       # EVPN configuration data
└── inventory/                  # Ansible inventory
```

## 🔄 Available Workflows

### Day 0 - Foundation Setup
- **Site Hierarchy**: Create and manage site topology
- **Network Settings**: Configure global network parameters
- **Device Credentials**: Manage device authentication
- **ISE Integration**: Configure RADIUS/AAA integration

### Day 1 - Device Management
- **Device Discovery**: Automated device discovery and onboarding
- **Device Templates**: Configuration template management
- **Provision**: Device provisioning and configuration deployment
- **PnP (Plug and Play)**: Zero-touch device provisioning

### Day 2 - Fabric Operations
- **SDA Fabric Sites**: Software-Defined Access fabric creation
- **SDA Virtual Networks**: L2/L3 gateway configuration
- **SDA Host Onboarding**: Endpoint policy management
- **LAN Automation**: Automated underlay deployment

### Operations & Maintenance
- **Device Backup**: Configuration backup automation
- **SWIM**: Software image management
- **Network Compliance**: Configuration compliance checking
- **Assurance**: Network health monitoring and analytics

## 🚀 Quick Start Examples

### 1. Site Hierarchy Setup
```bash
# Navigate to site hierarchy workflow
cd catalyst-center-iac/workflows/site_hierarchy

# Review the sample configuration
cat vars/site_hierarchy_vars.yml

# Execute the playbook
ansible-playbook playbook/site_hierarchy_playbook.yml -i ../../../../inventory/hosts.yml
```

### 2. Device Discovery and Provisioning
```bash
# Device discovery
cd catalyst-center-iac/workflows/device_discovery
ansible-playbook playbook/device_discovery_playbook.yml -i ../../../../inventory/hosts.yml

# Device provisioning
cd ../provision
ansible-playbook playbook/provision_playbook.yml -i ../../../../inventory/hosts.yml
```

### 3. SDA Fabric Deployment
```bash
# Create SDA fabric sites
cd catalyst-center-iac/workflows/sda_fabric_sites_zones
ansible-playbook playbook/sda_fabric_sites_zones_playbook.yml -i ../../../../inventory/hosts.yml

# Configure virtual networks
cd ../sda_virtual_networks_l2l3_gateways
ansible-playbook playbook/sda_virtual_networks_l2l3_gateways_playbook.yml -i ../../../../inventory/hosts.yml
```

## 🔧 Integration with EVPN Deployment

### Combined Workflow Example
```bash
#!/bin/bash
# Complete EVPN deployment with Catalyst Center workflows

# 1. Setup site hierarchy
cd catalyst-center-iac/workflows/site_hierarchy
ansible-playbook playbook/site_hierarchy_playbook.yml -i ../../../../inventory/hosts.yml

# 2. Configure network settings
cd ../network_settings
ansible-playbook playbook/network_settings_playbook.yml -i ../../../../inventory/hosts.yml

# 3. Discover and provision devices
cd ../device_discovery
ansible-playbook playbook/device_discovery_playbook.yml -i ../../../../inventory/hosts.yml

cd ../provision
ansible-playbook playbook/provision_playbook.yml -i ../../../../inventory/hosts.yml

# 4. Deploy EVPN fabric (project-specific)
cd ../../../../playbooks
ansible-playbook evpn_deployment.yml -i ../inventory/hosts.yml

# 5. Configure SDA fabric
cd ../catalyst-center-iac/workflows/sda_fabric_sites_zones
ansible-playbook playbook/sda_fabric_sites_zones_playbook.yml -i ../../../../inventory/hosts.yml
```

## 📝 Configuration Customization

### Using Project Variables
Each workflow includes:
- **vars/**: Sample variable files
- **schema/**: Input validation schemas
- **jinja_template/**: Dynamic configuration templates

### Example: Customizing Site Hierarchy
```yaml
# catalyst-center-iac/workflows/site_hierarchy/vars/site_hierarchy_vars.yml
sites:
  - site_name: "Global"
    site_type: "area"
    parent_site_name: ""
    
  - site_name: "USA"
    site_type: "area"
    parent_site_name: "Global"
    
  - site_name: "San Jose"
    site_type: "building"
    parent_site_name: "USA"
    address: "170 West Tasman Drive, San Jose, CA 95134, USA"
```

## 🔍 Input Validation

All workflows include Yamale-based validation schemas:

```bash
# Validate input before execution
cd catalyst-center-iac/workflows/site_hierarchy
yamale -s schema/site_hierarchy_schema.yml vars/site_hierarchy_vars.yml
```

## 📚 Documentation

Each workflow includes comprehensive documentation:
- **README.md**: Detailed usage instructions
- **description.json**: Workflow metadata
- **images/**: Visual guides and diagrams

### Key Documentation Links
- [Site Hierarchy](catalyst-center-iac/workflows/site_hierarchy/README.md)
- [Device Discovery](catalyst-center-iac/workflows/device_discovery/README.md)
- [SDA Fabric Management](catalyst-center-iac/workflows/sda_fabric_sites_zones/README.md)
- [ISE Integration](catalyst-center-iac/workflows/ise_radius_integration/README.md)

## 🔄 Updating the Submodule

To get the latest updates from the Catalyst Center IaC repository:

```bash
# Update submodule to latest version
git submodule update --remote catalyst-center-iac

# Commit the update
git add catalyst-center-iac
git commit -m "Update catalyst-center-iac submodule to latest version"
```

## 🎯 Best Practices

### 1. Workflow Sequencing
Follow the logical order for complete deployments:
1. Site hierarchy and network settings
2. Device credentials and discovery
3. Device provisioning and templates
4. Fabric configuration (SDA/EVPN)
5. Policy and security configuration

### 2. Variable Management
- Use consistent naming conventions across workflows
- Leverage Jinja2 templates for dynamic configurations
- Validate all inputs using provided schemas

### 3. Error Handling
- Always validate inputs before execution
- Use check mode for dry runs: `--check`
- Monitor Catalyst Center task status during execution

### 4. Integration Points
- Align site names between EVPN and SDA configurations
- Ensure device credentials are consistent across workflows
- Coordinate IP addressing schemes between underlay and overlay

## 🔧 Troubleshooting

### Common Issues
1. **Submodule not initialized**: Run `git submodule update --init --recursive`
2. **Missing dependencies**: Install requirements from both repositories
3. **Variable conflicts**: Use unique variable names or namespaces
4. **Authentication errors**: Verify Catalyst Center credentials and permissions

### Debug Mode
Enable verbose output for troubleshooting:
```bash
ansible-playbook playbook.yml -vvv
```

## 📞 Support

- **EVPN-specific issues**: Use this repository's issue tracker
- **Catalyst Center workflows**: Refer to the [upstream repository](https://github.com/cisco-en-programmability/catalyst-center-ansible-iac)
- **General Ansible questions**: Consult Ansible documentation

---

This integration provides a complete automation solution combining EVPN-specific workflows with comprehensive Catalyst Center management capabilities.
