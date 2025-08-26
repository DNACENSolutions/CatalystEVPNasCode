# Catalyst Center EVPN as Code

Automated BGP EVPN fabric deployment using Catalyst Center (DNAC) and Ansible workflows. This project provides complete automation for multi-site EVPN-VXLAN fabric deployment including underlay configuration, overlay provisioning, and 802.1X authentication integration.

## 🚀 Features

- **Complete EVPN Automation**: End-to-end BGP EVPN-VXLAN fabric deployment
- **Multi-Site Support**: Deploy and manage multiple sites with site-specific configurations
- **ISE Integration**: Built-in 802.1X authentication with Cisco ISE
- **Template-Driven**: Jinja2 templates for consistent device configuration
- **Catalyst Center Integration**: Uses only existing Catalyst Center Ansible roles
- **Validation & Verification**: Automated underlay and overlay validation
- **Data-Driven**: Single YAML file for all site configurations

## 📋 Prerequisites

### Software Requirements
- Ansible >= 6.0.0
- Python >= 3.8
- Cisco DNAC Ansible Collection

### Infrastructure Requirements
- Catalyst Center (DNAC) >= 2.3.7.6
- Cisco ISE for 802.1X authentication
- Catalyst 9000 series switches
- Network connectivity between Ansible control node and Catalyst Center

## 🛠 Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd CatalystEVPNasCode
   ```

2. **Install Python requirements:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Ansible collections:**
   ```bash
   ansible-galaxy collection install cisco.dnac
   ```

4. **Set up environment variables:**
   ```bash
   export CATALYST_CENTER_HOSTNAME="your-dnac-hostname"
   export CATALYST_CENTER_USERNAME="admin"
   export CATALYST_CENTER_PASSWORD="${CATALYST_CENTER_PASSWORD:?Set this from a secret manager}"
   ```

## 📖 Configuration

### Main Configuration File

Edit `data/sites.yml` to define your fabric configuration:

```yaml
global_settings:
  catalyst_center:
    hostname: "dnac.example.com"
    username: "admin"
    password: "{{ vault_device_password }}"
  
  ise_integration:
    primary_server_address: "10.1.1.100"
    shared_secret: "{{ vault_ise_radius_shared_secret }}"
  
  credentials:
    cli_credentials:
      - credential_name: "EVPN_CLI_CRED"
        username: "admin"
        password: "{{ vault_device_password }}"

sites:
  - site_name: "SITE_NYC"
    site_hierarchy: "Global/USA/NewYork/Building1"
    devices:
      borders: [...]
      spines: [...]
      leafs: [...]
    vlans: [...]
    vrfs: [...]
```

## 🚀 Deployment

### Complete Fabric Deployment

Deploy the entire EVPN fabric across all sites:

```bash
ansible-playbook evpn_deployment.yml
```

### Phase-by-Phase Deployment

Deploy specific phases using tags:

```bash
# Phase 1: ISE Integration
ansible-playbook evpn_deployment.yml --tags "phase1,ise"

# Phase 2: Site Hierarchy
ansible-playbook evpn_deployment.yml --tags "phase2,sites"

# Phase 3: Global Credentials
ansible-playbook evpn_deployment.yml --tags "phase3,credentials"

# Phase 4: Network Settings
ansible-playbook evpn_deployment.yml --tags "phase4,network"

# Phase 5: IP Pools
ansible-playbook evpn_deployment.yml --tags "phase5,pools"

# Phase 6: Device Discovery
ansible-playbook evpn_deployment.yml --tags "phase6,discovery"

# Phase 7: Site Assignment
ansible-playbook evpn_deployment.yml --tags "phase7,assignment"

# Phase 8: LAN Automation
ansible-playbook evpn_deployment.yml --tags "phase8,automation"

# Phase 9: Device Provisioning
ansible-playbook evpn_deployment.yml --tags "phase9,provision"

# Phase 10: Template Creation
ansible-playbook evpn_deployment.yml --tags "phase10,templates"

# Phase 11: Template Deployment
ansible-playbook evpn_deployment.yml --tags "phase11,deploy"

# Phase 12: Validation
ansible-playbook evpn_deployment.yml --tags "phase12,validate"
```

## 📁 Project Structure

```
CatalystEVPNasCode/
├── evpn_deployment.yml          # Master deployment playbook
├── data/
│   └── sites.yml                # Complete site configuration
├── playbooks/                   # Phase-specific playbooks
│   ├── 01_ise_integration.yml
│   ├── 02_site_design.yml
│   ├── 03_global_credentials.yml
│   ├── 04_network_settings.yml
│   ├── 05_ip_pools.yml
│   ├── 06_device_discovery.yml
│   ├── 07_site_assignment.yml
│   ├── 08_lan_automation.yml
│   ├── 09_device_provisioning.yml
│   ├── 10_template_creation.yml
│   ├── 11_template_deployment.yml
│   └── 12_validation.yml
├── templates/
│   └── overlay/                 # Jinja2 configuration templates
│       ├── border_evpn_config.j2
│       ├── spine_evpn_config.j2
│       ├── leaf_evpn_config.j2
│       └── dot1x_config.j2
├── roles/                       # Catalyst Center Ansible roles
└── vars/
    └── global.yml               # Global variables
```

## 🔧 Templates

### EVPN Configuration Templates

- **Border Template** (`border_evpn_config.j2`): EVPN border/edge device configuration
- **Spine Template** (`spine_evpn_config.j2`): BGP route reflector and underlay routing
- **Leaf Template** (`leaf_evpn_config.j2`): VTEP configuration and access ports
- **802.1X Template** (`dot1x_config.j2`): IEEE 802.1X authentication with ISE

### Template Features

- Dynamic VNI assignment
- BGP EVPN route target configuration
- Anycast gateway configuration
- Multicast underlay support
- 802.1X with MAB fallback
- Guest VLAN and critical auth VLAN
- DHCP snooping and DAI

## 🔍 Validation

After deployment, the automation validates:

- **Underlay Connectivity**: ISIS/OSPF adjacencies and reachability
- **Overlay Status**: BGP EVPN sessions and route advertisement
- **Device Inventory**: All devices properly discovered and provisioned
- **Template Deployment**: Configuration templates successfully applied

## 📊 Monitoring

Monitor your EVPN fabric through:

- Catalyst Center Dashboard
- BGP EVPN route monitoring
- VXLAN tunnel status
- 802.1X authentication logs
- Site-specific health metrics

## 🔧 Troubleshooting

### Common Issues

1. **Discovery Failures**: Check network connectivity and credentials
2. **Template Deployment**: Verify device compatibility and template syntax
3. **BGP EVPN Issues**: Validate ASN configuration and route targets
4. **802.1X Problems**: Check ISE connectivity and shared secrets

### Debug Mode

Enable debug mode for detailed logging:

```yaml
global_settings:
  catalyst_center:
    debug: true
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Open an issue in the repository
- Check Catalyst Center documentation
- Review Ansible collection documentation

## 📈 Roadmap

- [ ] Multi-tenancy support
- [ ] IPv6 underlay support
- [ ] SD-Access integration
- [ ] Automated testing framework
- [ ] Performance optimization
- [ ] Enhanced monitoring integration

---

**Note**: This project uses only existing Catalyst Center Ansible roles and does not require custom modules or plugins.
