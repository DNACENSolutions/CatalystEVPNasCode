# Catalyst Center EVPN as Code

Automated BGP EVPN fabric deployment using Catalyst Center (DNAC) and Ansible workflows. This project provides complete automation for multi-site EVPN-VXLAN fabric deployment including underlay configuration, overlay provisioning, and 802.1X authentication integration.

## 🚀 Features

- **Complete EVPN Automation**: End-to-end BGP EVPN-VXLAN fabric deployment
- **Multi-Site Support**: Deploy and manage multiple sites with site-specific configurations
- **ISE Integration**: Built-in 802.1X authentication with Cisco ISE
- **Template-Driven**: Jinja2 templates for consistent device configuration
- **Catalyst Center Integration**: Uses Cisco DNAC Ansible collection
- **Validation & Verification**: Pre-deployment validation with comprehensive schema checking
- **Data-Driven**: YAML-based configuration with validation
- **IPv4/IPv6 Dual Stack**: Support for both IPv4 and IPv6 addressing

## 📋 Prerequisites

### Software Requirements
- Ansible >= 6.0.0 (Ansible Core >= 2.13.0)
- Python >= 3.8
- Cisco DNAC Ansible Collection >= 6.7.0

### Infrastructure Requirements
- Catalyst Center (DNAC) >= 2.3.7.6
- Cisco ISE for 802.1X authentication
- Catalyst 9000 series switches
- Network connectivity between Ansible control node and Catalyst Center

## 🛠 Installation

1. **Clone the repository:**
   ```bash
   git clone git@github.com:DNACENSolutions/CatalystEVPNasCode.git
   cd CatalystEVPNasCode
   ```

2. **Install Python requirements:**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-validation.txt
   ```

3. **Install Ansible collections and roles:**
   ```bash
   ansible-galaxy collection install cisco.dnac
   git clone git@github.com:DNACENSolutions/catalyst_center_ansible_roles.git
   ```

4. **Set up environment variables:**
   ```bash
   export HOSTNAME="your-dnac-hostname"
   export USERNAME="admin"
   export PASSWORD="your-password"
   ```

## 📖 Configuration

### Group Variables Structure

The project uses a structured approach with group variables organized by function:

```
inventory/group_vars/
├── all/
│   └── global.yml                    # Global deployment settings
└── catalyst_center/
    ├── main.yml                      # Main control variables
    ├── ise_integration.yml           # ISE AAA integration
    ├── site_design.yml               # Site hierarchy design
    ├── credentials.yml               # Device credentials
    ├── network_settings.yml          # Network settings per site
    ├── ip_pools.yml                  # IP pool management
    ├── discovery.yml                 # Device discovery settings
    ├── provision.yml                 # Device provisioning
    └── templates.yml                 # Template creation
```

### Main Configuration Files

#### Site Design (`inventory/group_vars/catalyst_center/site_design.yml`)
```yaml
design_sites:
  - site:
      area:
        name: USA
        parent_name: Global
    type: area
  - site:
      building:
        name: BLD23
        parent_name: Global/USA/SAN JOSE
        address: "123 Main St, San Jose, CA"
        country: "United States"
        latitude: 37.3382
        longitude: -121.8863
    type: building
```

#### Device Credentials (`inventory/group_vars/catalyst_center/credentials.yml`)
```yaml
device_credentials:
  - global_credential_details:
      cli_credential:
        - description: switchandwlc credentials
          username: wlcaccess
          password: Lablab#123
          enable_password: Cisco#123
      snmp_v3:
        - description: snmpV3 Sample 1
          username: admin
          auth_type: SHA
          snmp_mode: AUTHPRIV
          privacy_type: AES128
```

#### ISE Integration (`inventory/group_vars/catalyst_center/ise_integration.yml`)
```yaml
ise_radius_integration_details:
  - authentication_policy_server:
    - server_type: ISE
      server_ip_address: 10.195.243.126
      shared_secret: Maglev123
      protocol: RADIUS
      role: primary
```

## 🚀 Deployment

### Validation First
Always validate your configuration before deployment:

```bash
# Validate BGP EVPN configuration
python validate_bgp_evpn_deployment.py data/bgp_evpn_site_01.yml

# Validate group variables
python validate_group_vars.py

# Or use make targets
make validate
```

### Complete Fabric Deployment

Deploy the entire EVPN fabric:

```bash
# Using the deployment script
./deploy.sh deploy

# Or directly with ansible-playbook
ansible-playbook playbooks/evpn_deployment.yml
```

### Phase-by-Phase Deployment

Deploy specific phases using the deployment script:

```bash
# Phase 1: ISE Integration
./deploy.sh phase1

# Phase 2: Site Hierarchy Design
./deploy.sh phase2

# Phase 3: Global Credentials
./deploy.sh phase3

# Phase 4: Network Settings
./deploy.sh phase4

# Phase 5: IP Pool Management
./deploy.sh phase5

# Phase 6: Device Discovery
./deploy.sh phase6

# Phase 9: Device Provisioning
./deploy.sh phase9

# Phase 10: Template Creation
./deploy.sh phase10
```

### Using Ansible Tags

Deploy specific components using tags:

```bash
# ISE Integration
ansible-playbook playbooks/evpn_deployment.yml --tags "ise"

# Site Design
ansible-playbook playbooks/evpn_deployment.yml --tags "sites"

# Credentials
ansible-playbook playbooks/evpn_deployment.yml --tags "credentials"

# Network Settings
ansible-playbook playbooks/evpn_deployment.yml --tags "network"

# IP Pools
ansible-playbook playbooks/evpn_deployment.yml --tags "ippools"

# Device Discovery
ansible-playbook playbooks/evpn_deployment.yml --tags "discovery"

# Device Provisioning
ansible-playbook playbooks/evpn_deployment.yml --tags "provision"

# Template Creation
ansible-playbook playbooks/evpn_deployment.yml --tags "templates"

# All validation steps
ansible-playbook playbooks/evpn_deployment.yml --tags "validate"
```

## 📁 Project Structure

```
CatalystEVPNasCode/
├── data/
│   └── bgp_evpn_site_01.yml         # Sample BGP EVPN configuration
├── playbooks/
│   └── evpn_deployment.yml          # Master deployment playbook
├── inventory/
│   ├── hosts.yml                    # Ansible inventory
│   └── group_vars/                  # Structured group variables
│       ├── all/
│       │   └── global.yml           # Global settings
│       └── catalyst_center/
│           ├── ise_integration.yml  # ISE configuration
│           ├── site_design.yml      # Site hierarchy
│           ├── credentials.yml      # Device credentials
│           ├── network_settings.yml # Network settings
│           ├── ip_pools.yml         # IP pool management
│           ├── discovery.yml        # Device discovery
│           ├── provision.yml        # Device provisioning
│           └── templates.yml        # Template definitions
├── schemas/
│   └── group_vars/                  # JSON schemas for validation
│       ├── bgp_evpn_deployment.json # BGP EVPN validation schema
│       ├── site_design.json         # Site design validation
│       ├── credentials.json         # Credentials validation
│       └── ise_integration.json     # ISE validation
├── templates/
│   └── overlay/                     # Jinja2 configuration templates
│       ├── border_evpn_config.j2
│       ├── spine_evpn_config.j2
│       ├── leaf_evpn_config.j2
│       └── dot1x_config.j2
├── roles/                           # Catalyst Center Ansible roles
├── validate_bgp_evpn_deployment.py  # BGP EVPN validation script
├── validate_group_vars.py           # Group variables validation
├── deploy.sh                        # Deployment script
├── Makefile                         # Make targets for validation
└── BGP_EVPN_VALIDATION_GUIDE.md     # Validation documentation
```

## 🔧 Templates

### EVPN Configuration Templates

The project includes comprehensive Jinja2 templates for EVPN configuration:

- **Border Template** (`EVPN_Border_Template`): EVPN border/edge device configuration
- **Spine Template** (`EVPN_Spine_Template`): BGP route reflector and underlay routing  
- **Leaf Template** (`EVPN_Leaf_Template`): VTEP configuration and access ports
- **802.1X Template** (`Dot1X_Access_Template`): IEEE 802.1X authentication with ISE

### Template Features

- Dynamic BGP AS number configuration
- VXLAN NVE interface configuration
- BGP EVPN address family settings
- 802.1X with RADIUS authentication
- Template versioning and project organization

## 🔍 Validation

The project includes comprehensive validation capabilities:

### Pre-Deployment Validation

```bash
# Validate BGP EVPN configuration
python validate_bgp_evpn_deployment.py data/bgp_evpn_site_01.yml

# Validate with JSON output
python validate_bgp_evpn_deployment.py data/bgp_evpn_site_01.yml --json-output

# Validate group variables
python validate_group_vars.py
```

### Validation Components

- **Schema Validation**: JSON Schema-based validation for configuration structure
- **IP Address Validation**: Comprehensive IP address format and validity checks
- **Site Hierarchy Validation**: Ensures proper site naming and parent-child relationships
- **Credentials Consistency**: Validates credential definitions and assignments
- **ISE Integration Validation**: Checks ISE server configuration and RADIUS settings

### Automated Validation

The deployment script includes automatic validation:

```bash
# Validation is automatically run before deployment
./deploy.sh deploy
```

## 📊 IP Pool Management

The project supports comprehensive IP pool management with:

- **Global Pools**: Centralized IP pool definitions
- **Site-Specific Pools**: Reserved pools for each site
- **IPv4/IPv6 Dual Stack**: Support for both address families
- **DHCP/DNS Integration**: Automatic server configuration
- **Pool Types**: Generic, LAN, and specialized pool types

### Example IP Pool Configuration

```yaml
ipam_details:
- global_pool_details:
    settings:
      ip_pool:
      - name: EMPLOYEEPOOL
        gateway: 192.168.0.1
        ip_address_space: IPv4
        cidr: 192.168.0.0/16
        pool_type: Generic
        dhcp_server_ips:
        - 204.192.3.40
        dns_server_ips:
        - 171.70.168.183
```

## 🔧 Troubleshooting

### Common Issues

1. **Validation Failures**: Check configuration syntax and required fields
2. **Discovery Failures**: Verify network connectivity and credentials
3. **Template Issues**: Validate template syntax and device compatibility
4. **ISE Integration**: Check ISE connectivity and shared secrets

### Debug Mode

Enable verbose logging for troubleshooting:

```bash
# Enable debug mode in deploy.sh
./deploy.sh deploy  # Already includes -vvvv for detailed output

# Or with ansible-playbook
ansible-playbook playbooks/evpn_deployment.yml -vvvv
```

### Validation Logs

The validation system provides detailed error reporting:

```bash
# Run validation with detailed output
python validate_bgp_evpn_deployment.py data/bgp_evpn_site_01.yml

# Check validation guide for troubleshooting
cat BGP_EVPN_VALIDATION_GUIDE.md
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run validation tests: `make validate`
5. Test thoroughly in lab environment
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Open an issue in the repository
- Check the BGP_EVPN_VALIDATION_GUIDE.md for validation help
- Review Catalyst Center documentation
- Consult the DEPLOYMENT_GUIDE.md for detailed deployment instructions

## 📈 Roadmap

- [x] BGP EVPN validation system
- [x] Comprehensive schema validation
- [x] IPv4/IPv6 dual stack support
- [x] Template-based configuration
- [ ] Multi-tenancy support
- [ ] SD-Access integration
- [ ] Automated testing framework
- [ ] Performance optimization
- [ ] Enhanced monitoring integration

---

**Note**: This project uses the Cisco DNAC Ansible collection and provides comprehensive validation and deployment automation for BGP EVPN fabrics.
