# Group Variables Structure

This directory contains the organized group variables for the CatalystEVPNasCode project. The variables are structured to support the complete BGP EVPN fabric deployment workflow.

## Directory Structure

```
inventory/group_vars/
├── all/
│   └── global.yml                    # Global variables for all hosts
└── catalyst_center/
    ├── main.yml                      # Main control variables
    ├── api.yml                       # Catalyst Center API settings
    ├── ise_integration.yml           # ISE AAA integration variables
    ├── site_design.yml               # Site hierarchy design variables
    ├── credentials.yml               # Device credentials configuration
    ├── network_settings.yml          # Network settings per site
    ├── ip_pools.yml                  # IP pool management variables
    ├── fabric.yml                    # Discovery, LAN automation, provisioning
    └── templates.yml                 # Template creation and deployment
```

## File Descriptions

### all/global.yml
Contains global variables that apply to all hosts and groups:
- Common Ansible settings
- EVPN fabric defaults
- Protocol defaults (ISIS, BGP, VXLAN)
- 802.1X defaults
- Common network settings

### catalyst_center/main.yml
Main control variables for deployment workflow:
- Phase control settings
- Deployment control options
- Rollback configuration
- Monitoring and validation settings

### catalyst_center/api.yml
Catalyst Center API connection settings:
- API version and connection parameters
- Common role defaults
- Logging and debugging settings

### catalyst_center/ise_integration.yml
ISE AAA integration configuration:
- Primary and secondary ISE servers
- RADIUS settings
- PxGrid configuration
- Integration timeouts

### catalyst_center/site_design.yml
Site hierarchy design variables:
- Area, building, and floor definitions
- Geographic information
- Site-specific settings

### catalyst_center/credentials.yml
Device credential management:
- CLI credentials
- SNMP v2/v3 credentials
- HTTPS credentials
- Credential assignment settings

### catalyst_center/network_settings.yml
Network settings per site:
- DNS, DHCP, NTP servers
- Syslog and SNMP settings
- Netflow collectors
- Site-specific overrides

### catalyst_center/ip_pools.yml
IP pool management configuration:
- Global and site-specific pools
- VLAN to pool mappings
- DHCP and DNS settings per pool
- VNI range settings

### catalyst_center/fabric.yml
Fabric-related configurations:
- Device discovery settings
- LAN automation parameters
- Site assignment details
- Provisioning configuration

### catalyst_center/templates.yml
Template management variables:
- EVPN configuration templates
- 802.1X authentication templates
- Template deployment targets
- Template parameters

## Usage

These variables are automatically loaded by Ansible based on the group membership defined in the inventory. The `catalyst_center` group will load all files from the `catalyst_center/` directory.

## Variable Precedence

Ansible variable precedence (highest to lowest):
1. Extra vars (`-e` command line)
2. Host vars
3. Group vars (catalyst_center)
4. Group vars (all)
5. Role defaults

## Customization

To customize the deployment:
1. Modify the appropriate variable file
2. Override specific variables in host_vars if needed
3. Use extra vars for temporary overrides

## Examples

### Running specific phases:
```bash
ansible-playbook playbooks/evpn_deployment.yml -t phase1,phase2
```

### Override deployment settings:
```bash
ansible-playbook playbooks/evpn_deployment.yml -e "phase_control.phase_01_ise_integration=false"
```

### Run in dry-run mode:
```bash
ansible-playbook playbooks/evpn_deployment.yml -e "deployment_control.dry_run=true"
```

## Validation

All variables should be validated before deployment. Use the included validation tasks to verify configuration consistency.
