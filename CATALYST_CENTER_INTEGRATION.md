# Catalyst Center Ansible IaC Integration

This project now includes comprehensive Catalyst Center automation resources via Git submodules, providing access to 30+ validated playbooks and extensive BGP EVPN VXLAN template collections for complete network automation.

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
├── catalyst-center-roles/        # Git submodule with standardized Ansible roles
│   ├── catalyst_center_device_discovery/     # Device discovery role
│   ├── catalyst_center_device_provision/     # Device provisioning role
│   ├── catalyst_center_sda_fabric/          # SDA fabric management role
│   ├── catalyst_center_network_settings/    # Network settings role
│   ├── catalyst_center_device_templates/    # Template management role
│   └── ... (30+ more roles)
├── playbooks/                   # Project-specific EVPN playbooks
├── data/                       # EVPN configuration data
│   ├── bgp_evpn_site_01.yml    # Site-specific configurations
│   └── catalyst-center-bgp-evpn-examples/  # BGP EVPN template collection
│       ├── BGP EVPN/           # Jinja2 templates for fabric deployment
│       ├── BGP_EVPN_rev2/      # Enhanced templates with IPSEC support
│       ├── EVPN_Project.json   # Catalyst Center project export
│       └── EVPN_Templates.json # Template definitions
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

## 🏗️ BGP EVPN Template Collection

The `data/catalyst-center-bgp-evpn-examples/` submodule provides comprehensive Jinja2 templates for Campus BGP EVPN VXLAN fabric deployment:

### Template Categories
- **FABRIC-* Templates**: Core fabric configuration templates
  - `FABRIC-VRF.j2`: VRF configuration for multi-tenancy
  - `FABRIC-LOOPBACKS.j2`: Loopback interface configuration
  - `FABRIC-NVE.j2`: Network Virtualization Edge (NVE) interfaces
  - `FABRIC-EVPN.j2`: BGP EVPN control plane configuration
  - `FABRIC-OVERLAY.j2`: VXLAN overlay network services
  - `FABRIC-MCAST.j2`: Multicast configuration for BUM traffic
  - `FABRIC-NAC-IOT.j2`: Network Access Control for IoT segments

- **DEFN-* Templates**: Definition and variable templates
  - `DEFN-ROLES.j2`: Device role definitions (spine/leaf/border)
  - `DEFN-VRF.j2`: VRF definitions and parameters
  - `DEFN-OVERLAY.j2`: Overlay network definitions
  - `DEFN-L3OUT.j2`: Layer 3 external connectivity

### Enhanced Features (BGP_EVPN_rev2)
- **IPSEC Support**: Hardware-accelerated encryption for tenant traffic
- **Multi-Cluster BGP EVPN**: Border switch integration
- **Advanced Multicast**: Optimized PIM configuration
- **IoT Segmentation**: Specialized templates for IoT tenant isolation

### Template Usage
```bash
# Import templates into Catalyst Center
# 1. Use EVPN_Project.json for complete project import
# 2. Use EVPN_Templates.json for individual template import
# 3. Customize Jinja2 templates in BGP EVPN/ or BGP_EVPN_rev2/ directories

# Example: Review fabric EVPN template
cat data/catalyst-center-bgp-evpn-examples/BGP_EVPN_rev2/FABRIC-EVPN.j2
```

## 🎭 Standardized Ansible Roles

The `catalyst-center-roles/` submodule provides a collection of standardized Ansible roles following unified design patterns:

### Role Design Principles
- **Standardized State Management**: All roles use `state` variable (`merged`/`deleted`) for CRUD operations
- **Simplified Variables**: Single list variable per role (e.g., `discovery_details`, `provision_details`)
- **Consistent Structure**: Each role follows the same directory structure and naming conventions
- **Comprehensive Documentation**: Detailed README with examples for each role

### Available Role Categories

#### **Device Management Roles**
- `catalyst_center_device_credentials`: Global device credentials management
- `catalyst_center_device_discovery`: Network discovery job automation
- `catalyst_center_device_inventory`: Device inventory management
- `catalyst_center_device_provision`: Device provisioning to sites
- `catalyst_center_device_templates`: Configuration template management

#### **Network Infrastructure Roles**
- `catalyst_center_network_settings`: Global network settings (NTP, SNMP, etc.)
- `catalyst_center_ipam`: IP pool and subnet management
- `catalyst_center_site_design`: Site hierarchy management (areas, buildings, floors)
- `catalyst_center_swim`: Software Image Management (SWIM)

#### **SDA Fabric Roles**
- `catalyst_center_sda_fabric`: SDA fabric creation and management
- `catalyst_center_sda_device_roles`: Device role assignment in SDA fabric
- `catalyst_center_sda_hostonboarding`: Host onboarding policies and anycast gateways
- `catalyst_center_sda_transits`: SDA transit network management
- `catalyst_center_sda_virtual_network_gateways`: Virtual network gateway management

#### **Security & Integration Roles**
- `catalyst_center_ise_aaa_integration`: ISE and AAA server integration
- `catalyst_center_user_role`: User roles and permissions management
- `catalyst_center_events_and_notifications`: Event and notification configuration

#### **Wireless & Access Point Roles**
- `catalyst_center_wireless_design`: Wireless network design
- `catalyst_center_accesspoints_configuration`: Access point configuration
- `catalyst_center_network_profile_wireless`: Wireless network profiles

### Role Usage Examples

#### Basic Role Usage Pattern
```yaml
---
- name: Configure device discovery
  ansible.builtin.include_role:
    name: catalyst_center_device_discovery
  vars:
    state: merged
    discovery_details:
      - discovery_name: "Site1-Discovery"
        ip_address_list: ["10.1.1.0/24"]
        discovery_type: "Range"
        protocol_order: "ssh,telnet"
        timeout: 5
        retry_count: 3
```

#### Advanced Multi-Role Playbook
```yaml
---
- name: Complete SDA Fabric Setup
  hosts: catalyst_center
  gather_facts: false
  tasks:
    - name: Configure network settings
      ansible.builtin.include_role:
        name: catalyst_center_network_settings
      vars:
        state: merged
        network_settings_details:
          - ntp_server: ["pool.ntp.org"]
            timezone: "America/New_York"
    
    - name: Create SDA fabric
      ansible.builtin.include_role:
        name: catalyst_center_sda_fabric
      vars:
        state: merged
        sda_fabric_details:
          - fabric_name: "Campus-Fabric"
            fabric_type: "FABRIC_SITE"
    
    - name: Assign device roles
      ansible.builtin.include_role:
        name: catalyst_center_sda_device_roles
      vars:
        state: merged
        sda_device_role_details:
          - device_ip: "10.1.1.10"
            role: "BORDER_NODE"
            fabric_name: "Campus-Fabric"
```

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
