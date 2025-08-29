# CatalystEVPNasCode - EVPN Fabric Deployment Guide

This comprehensive guide provides step-by-step instructions for deploying a BGP EVPN-VXLAN fabric across multiple sites using Catalyst Center and Ansible automation.

## 🏗️ Architecture Overview

### Multi-Site EVPN Fabric Architecture

```
                    ┌─────────────────────────────────────────────────┐
                    │              External Network                   │
                    │         (Internet/WAN/MPLS)                    │
                    └─────────────────┬───────────────────────────────┘
                                      │
                    ┌─────────────────┴───────────────────────────────┐
                    │           Catalyst Center (DNAC)               │
                    │         Management Platform                     │
                    └─────────────────┬───────────────────────────────┘
                                      │
                    ┌─────────────────┴───────────────────────────────┐
                    │               ISE Server                        │
                    │        802.1X Authentication                    │
                    └─────────────────────────────────────────────────┘

    Site NYC (AS 65001)                           Site LA (AS 65002)
    ┌─────────────────────────┐                  ┌─────────────────────────┐
    │    NYC-BORDER-01/02     │◄────────────────►│    LA-BORDER-01        │
    │    (VTEP Gateways)      │   eBGP EVPN      │   (VTEP Gateway)       │
    └──────────┬──────────────┘   Inter-site     └──────────┬─────────────┘
               │              │   Connectivity               │
    ┌──────────┴──────────────┐                  ┌──────────┴─────────────┐
    │   NYC-SPINE-01/02       │                  │    LA-SPINE-01         │
    │   (Route Reflectors)    │                  │  (Route Reflector)     │
    └─────┬─────────────┬─────┘                  └─────┬──────────────────┘
          │             │                              │
    ┌─────┴─────┐ ┌─────┴─────┐              ┌─────────┴─────┐
    │NYC-LEAF-01│ │NYC-LEAF-03│              │  LA-LEAF-01   │
    │NYC-LEAF-02│ │NYC-LEAF-04│              │  LA-LEAF-02   │
    │ (VTEPs)   │ │ (VTEPs)   │              │   (VTEPs)     │
    └─────┬─────┘ └─────┬─────┘              └─────┬─────────┘
          │             │                          │
    ┌─────┴─────┐ ┌─────┴─────┐              ┌─────┴─────────┐
    │  Floor1   │ │  Floor2   │              │    Floor1     │
    │ Endpoints │ │ Endpoints │              │   Endpoints   │
    └───────────┘ └───────────┘              └───────────────┘
```

### Network Addressing Plan

#### Global Addressing Scheme
```
Management Network:     10.1.0.0/16 (Global Pool)
Loopback Network:       10.255.0.0/16 (Global Pool)
P2P Network:           10.254.0.0/16 (Global Pool)

Site NYC (AS 65001):
- Management:          10.1.1.0/24
- Underlay Loopback:   10.10.0.0/24
- Underlay P2P:        10.10.1.0/24
- VTEP Pool:           10.10.2.0/24
- Data VLANs:          192.168.100.0/24, 192.168.200.0/24
- Guest VLAN:          192.168.300.0/24

Site LA (AS 65002):
- Management:          10.2.1.0/24
- Underlay Loopback:   10.20.0.0/24
- Underlay P2P:        10.20.1.0/24
- VTEP Pool:           10.20.2.0/24
- Data VLANs:          192.168.100.0/24 (stretched)
```

### VNI and VLAN Mapping
```
VLAN 100 (DATA_VLAN)    ↔ VNI 10100 ↔ VRF DATA_VRF (VNI 50001)
VLAN 200 (VOICE_VLAN)   ↔ VNI 10200 ↔ VRF DATA_VRF (VNI 50001)
VLAN 300 (GUEST_VLAN)   ↔ VNI 10300 ↔ VRF GUEST_VRF (VNI 50002)
```

## 📋 Pre-Deployment Checklist

### Infrastructure Requirements

- [ ] **Catalyst Center (DNAC)** - Version 2.3.7.6 or later, accessible via HTTPS
- [ ] **Cisco ISE Server** - Configured for RADIUS authentication
- [ ] **Network Devices** - Catalyst 9000 series switches with IOS-XE
- [ ] **Management Network** - Layer 3 connectivity to all devices
- [ ] **SSH Access** - Configured on seed devices with proper credentials
- [ ] **Physical Connectivity** - All spine-leaf connections established

### Software Requirements

```bash
# Required Software Versions
Ansible Core:           >= 2.13.0
Python:                >= 3.8
Catalyst Center:       >= 2.3.7.6
Cisco DNAC Collection: Latest version
```

### Credential Requirements

- [ ] **DNAC Administrator** - Full admin access to Catalyst Center
- [ ] **Device CLI Credentials** - Username/password for all network devices  
- [ ] **SNMP Communities** - Read and write community strings
- [ ] **ISE Shared Secret** - RADIUS authentication shared secret
- [ ] **Enable Passwords** - Privilege escalation passwords

### Site Planning Checklist

- [ ] **Site Hierarchy** - Global > Area > Building > Floor structure defined
- [ ] **IP Addressing** - Non-overlapping subnets for each site
- [ ] **BGP AS Numbers** - Unique AS numbers per site (65001, 65002, etc.)
- [ ] **Device Roles** - Border, Spine, Leaf assignments planned
- [ ] **VLAN/VNI Design** - Layer 2/3 segmentation requirements mapped
- [ ] **Physical Topology** - Cabling and port assignments documented

## 🚀 Installation and Setup

### Step 1: Environment Preparation

1. **Clone the Repository:**
   ```bash
   git clone git@github.com:DNACENSolutions/CatalystEVPNasCode.git
   cd CatalystEVPNasCode
   ```

2. **Install Python Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Ansible Collections and Roles:**
   ```bash
   ansible-galaxy collection install cisco.dnac
   ansible-galaxy collection install -r role_requirements.yml
   ```

4. **Set Environment Variables:**
   ```bash
   export HOSTNAME="your-dnac-hostname.domain.com"
   export USERNAME="admin"
   export PASSWORD="${CATALYST_CENTER_PASSWORD:?Set this from a secret manager}"
   ```

### Step 2: Configuration Customization

#### 2.1 Site Configuration (`data/sites.yml`)

The main configuration file contains all site-specific settings. Key sections to customize:

**Global Settings:**
```yaml
global_settings:
  catalyst_center:
    hostname: "dnac.yourcompany.com"
    username: "admin"
    password: "{{ vault_device_password }}"
  
  ise_integration:
    primary_server_address: "10.1.1.100"
    shared_secret: "{{ vault_ise_radius_shared_secret }}"
```

**Site-Specific Configuration:**
```yaml
sites:
  - site_name: "SITE_NYC"
    site_hierarchy: "Global/USA/NewYork/Building1"
    devices:
      borders: [...]  # Update with your border devices
      spines: [...]   # Update with your spine devices  
      leafs: [...]    # Update with your leaf devices
```

#### 2.2 Device Inventory

Update device inventory with your actual hardware:

```yaml
devices:
  borders:
    - hostname: "NYC-BORDER-01"
      management_ip: "10.1.1.101"    # Your actual management IP
      loopback0: "10.10.0.1"         # Underlay loopback
      vtep_ip: "10.10.2.1"           # VTEP source IP
      asn: 65001                     # Site BGP AS number
      role: "border"
      site: "Global/USA/NewYork/Building1"
```

## 🔧 Deployment Execution

### Option 1: Complete Automated Deployment

Execute the entire EVPN fabric deployment:

```bash
./deploy.sh deploy
```

This executes all 12 phases sequentially:
1. ISE Integration
2. Site Hierarchy Design  
3. Global Credentials
4. Network Settings
5. IP Pool Management
6. Device Discovery
7. Site Assignment
8. LAN Automation
9. Device Provisioning
10. Template Creation
11. Template Deployment
12. Validation

### Option 2: Phase-by-Phase Deployment

Execute individual phases for granular control:

```bash
# Phase 1: Configure ISE Integration
./deploy.sh phase1

# Phase 2: Create Site Hierarchy
./deploy.sh phase2

# Phase 8: Execute LAN Automation (Critical Phase)
./deploy.sh phase8

# Phase 11: Deploy EVPN Templates (Critical Phase)
./deploy.sh phase11

# Phase 12: Validate Deployment
./deploy.sh validate
```

### Critical Phases Monitoring

#### Phase 8: LAN Automation ⚠️
**Duration: 15-30 minutes**
**Monitoring Required:**
- Watch DNAC LAN Automation dashboard
- Monitor device discovery progress
- Verify underlay IP assignments
- Check ISIS adjacency formation

```bash
# Monitor LAN automation progress
tail -f /var/log/ansible.log
```

#### Phase 11: Template Deployment ⚠️
**Duration: 20-45 minutes**  
**Critical Monitoring:**
- Device configuration changes
- BGP session establishment
- VXLAN tunnel formation
- Service disruption window

```bash
# Monitor template deployment
./deploy.sh phase11 -vvv
```

## 🏢 Site Topology Details

### NYC Site Topology

```
                         Management Network
                              10.1.1.0/24
                                   │
    ┌─────────────────────────────────────────────────────────┐
    │                                                         │
    │  NYC-BORDER-01          NYC-BORDER-02                   │
    │  10.1.1.101            10.1.1.102                      │
    │  Lo0: 10.10.0.1        Lo0: 10.10.0.2                  │
    │  VTEP: 10.10.2.1       VTEP: 10.10.2.2                 │
    │  ASN: 65001            ASN: 65001                       │
    └─────┬─────────────────────────────┬─────────────────────┘
          │ P2P: 10.10.1.0/30           │ P2P: 10.10.1.4/30
          │                             │
    ┌─────┴─────────────┐         ┌─────┴─────────────┐
    │                   │         │                   │
    │  NYC-SPINE-01     │         │  NYC-SPINE-02     │
    │  10.1.1.103       │         │  10.1.1.104       │
    │  Lo0: 10.10.0.3   │◄────────┤  Lo0: 10.10.0.4   │
    │  ASN: 65001       │         │  ASN: 65001       │
    │  (Route Reflector)│         │  (Route Reflector)│
    └─────┬─────────────┘         └─────┬─────────────┘
          │                             │
    ┌─────┼─────────────────────────────┼─────┐
    │     │                             │     │
    │  ┌──┴──┐  ┌──────┐           ┌──┴──┐  ┌──────┐
    │  │     │  │      │           │     │  │      │
    │  │ L01 │  │ L02  │           │ L03 │  │ L04  │
    │  │     │  │      │           │     │  │      │
    │  └─────┘  └──────┘           └─────┘  └──────┘
    │                                             │
    │  Floor 1                    Floor 2        │
    │  NYC-LEAF-01/02            NYC-LEAF-03/04   │
    │  VTEP: 10.10.2.5/6         VTEP: 10.10.2.7/8│
    │  VLANs: 100,200,300        VLANs: 100,200,300│
    └─────────────────────────────────────────────┘

    Access Layer:
    ├── VLAN 100: Data Network (192.168.100.0/24)
    ├── VLAN 200: Voice Network (192.168.200.0/24) 
    └── VLAN 300: Guest Network (192.168.300.0/24)
```

### LA Site Topology

```
                         Management Network  
                              10.2.1.0/24
                                   │
    ┌─────────────────────────────────────────────────────────┐
    │                                                         │
    │            LA-BORDER-01                                 │
    │            10.2.1.101                                   │
    │            Lo0: 10.20.0.1                               │
    │            VTEP: 10.20.2.1                              │
    │            ASN: 65002                                   │
    └─────────────────┬───────────────────────────────────────┘
                      │ P2P: 10.20.1.0/30
                      │
    ┌─────────────────┴───────────────────────────────────────┐
    │                                                         │
    │            LA-SPINE-01                                  │
    │            10.2.1.102                                   │
    │            Lo0: 10.20.0.2                               │  
    │            ASN: 65002                                   │
    │            (Route Reflector)                            │
    └─────┬─────────────────────────────────┬─────────────────┘
          │                                 │
    ┌─────┴─────────┐                 ┌─────┴─────────┐
    │               │                 │               │
    │   LA-LEAF-01  │                 │   LA-LEAF-02  │
    │   10.2.1.103  │                 │   10.2.1.104  │
    │   Lo0: 10.20.0.3                │   Lo0: 10.20.0.4  │
    │   VTEP: 10.20.2.3               │   VTEP: 10.20.2.4 │
    │   ASN: 65002  │                 │   ASN: 65002  │
    └───────────────┘                 └───────────────┘
            │                                 │
    ┌───────────────┐                 ┌───────────────┐
    │    Floor 1    │                 │    Floor 1    │
    │   Endpoints   │                 │   Endpoints   │
    │  VLANs: 100   │                 │  VLANs: 100   │
    └───────────────┘                 └───────────────┘
```

### Inter-Site Connectivity

```
    NYC Site                                    LA Site
    ┌─────────────────┐                         ┌─────────────────┐
    │  NYC-BORDER-01  │                         │   LA-BORDER-01  │
    │  NYC-BORDER-02  │◄─────────────────────► │                 │
    └─────────────────┘    eBGP EVPN           └─────────────────┘
           │                Multi-site                    │
           │                Connectivity                  │
    ┌─────────────────┐                         ┌─────────────────┐
    │  Layer 3 VNI    │                         │  Layer 3 VNI    │
    │  50001: DATA_VRF│◄─────────────────────► │  50001: DATA_VRF│
    │  50002: GUEST_VRF                         │  50002: GUEST_VRF│
    └─────────────────┘                         └─────────────────┘

    Route Target Exchange:
    ├── Data VRF:  RT 65001:50001 ↔ RT 65002:50001
    └── Guest VRF: RT 65001:50002 ↔ RT 65002:50002
```

## 🔍 Validation and Verification

### Automated Validation

Run comprehensive validation:
```bash
./deploy.sh validate
```

### Manual Verification Commands

#### On Spine Devices (Route Reflectors):
```bash
# BGP EVPN neighbor status
show bgp l2vpn evpn summary

# EVPN routes
show bgp l2vpn evpn

# ISIS adjacencies  
show isis neighbors

# Route reflection status
show bgp l2vpn evpn neighbors <leaf-ip> advertised-routes
```

#### On Leaf Devices (VTEPs):
```bash
# VXLAN tunnel status
show nve peers

# VNI status
show nve vni

# VTEP interface status  
show interface nve1

# MAC address learning
show l2route evpn mac all

# BGP EVPN routes received
show bgp l2vpn evpn
```

#### On Border Devices (DCI Gateways):
```bash
# Inter-site BGP status
show bgp l2vpn evpn summary

# External connectivity
show bgp l2vpn evpn neighbors

# VRF routing tables
show ip route vrf DATA_VRF
show ip route vrf GUEST_VRF
```

### Expected Validation Results

#### ✅ Successful Deployment Indicators:

1. **Underlay Validation:**
   - All ISIS adjacencies in "UP" state
   - Loopback reachability across fabric  
   - P2P link utilization balanced

2. **Overlay Validation:**
   - BGP EVPN sessions established
   - Type-2 (MAC/IP) routes advertised
   - Type-3 (IMET) routes present
   - VXLAN tunnels operational

3. **Access Validation:**
   - 802.1X authentication successful
   - Dynamic VLAN assignment working
   - Inter-VLAN routing functional
   - Guest isolation enforced

## 📊 Monitoring and Operations

### Catalyst Center Dashboard

Monitor fabric health through DNAC:

1. **Fabric Overview:**
   - Navigate to Provision > Fabric
   - View site topology and device status
   - Monitor underlay and overlay health

2. **Device Inventory:**
   - Check device compliance status
   - Review configuration drift
   - Monitor software versions

3. **Assurance Features:**
   - Use Intelligent Capture for troubleshooting
   - Run Path Trace for connectivity verification  
   - Monitor fabric performance metrics

### Key Performance Indicators (KPIs)

```yaml
Fabric Health Metrics:
├── Underlay Convergence: < 5 seconds
├── BGP EVPN Convergence: < 30 seconds  
├── VXLAN Tunnel Establishment: < 60 seconds
├── 802.1X Authentication: < 10 seconds
└── Inter-site Latency: Baseline + monitoring
```

### Operational Procedures

#### Regular Health Checks:
```bash
# Daily validation
./deploy.sh validate

# Weekly configuration backup
ansible-playbook playbooks/backup_configs.yml

# Monthly template updates
git pull && ./deploy.sh phase10
```

## 🚨 Troubleshooting Guide

### Common Issues and Solutions

#### 1. Device Discovery Failures
**Symptoms:**
- Devices not appearing in DNAC inventory
- LAN automation stuck or failing

**Solutions:**
```bash
# Check device connectivity
ping <device-management-ip>

# Verify SSH access
ssh admin@<device-ip>

# Check CDP/LLDP
show cdp neighbors
show lldp neighbors detail
```

#### 2. BGP EVPN Session Issues
**Symptoms:**
- BGP sessions in "Active" or "Connect" state
- Missing EVPN routes

**Solutions:**
```bash
# Check BGP configuration
show bgp l2vpn evpn summary
show bgp l2vpn evpn neighbors <peer-ip>

# Verify reachability
ping <peer-loopback-ip> source <local-loopback>

# Check route reflector configuration
show bgp l2vpn evpn neighbors <client-ip> advertised-routes
```

#### 3. VXLAN Tunnel Problems
**Symptoms:**
- No VXLAN tunnels established
- Traffic not crossing VXLAN

**Solutions:**
```bash
# Check NVE interface
show interface nve1

# Verify VTEP peers
show nve peers

# Check multicast underlay
show ip mroute
show ip pim neighbor
```

#### 4. 802.1X Authentication Failures
**Symptoms:**
- Clients not authenticating
- Stuck in wrong VLAN

**Solutions:**
```bash
# Check ISE connectivity
test aaa group radius <username> <password> legacy

# Review authentication sessions
show authentication sessions

# Check RADIUS statistics  
show radius statistics
```

### Log Collection and Analysis

```bash
# Collect Ansible logs
cat ansible.log | grep ERROR

# Export DNAC configurations
# Use DNAC GUI: System Settings > Backup & Restore

# Collect device logs
show logging | include ERROR|WARN

# Generate debug logs
debug bgp l2vpn evpn
debug nve
```

## 📞 Support Escalation

### Internal Escalation Path

1. **Level 1**: Network Operations Team
2. **Level 2**: Network Engineering Team  
3. **Level 3**: Architecture Team

### External Support

1. **Cisco TAC**: For platform-specific issues
2. **Professional Services**: For complex deployments
3. **Partner Support**: For third-party integrations

### Documentation Requirements

- Network topology diagrams
- Configuration backups  
- Error logs and screenshots
- Timeline of events
- Business impact assessment

---

## ⚠️ Important Notes

- **Always test in lab environment** before production deployment
- **Schedule maintenance windows** for critical phases (8, 11)
- **Maintain rollback procedures** for each deployment phase
- **Document all customizations** made to templates and configurations
- **Keep credentials secure** using Ansible Vault or external secret management

## 📚 Additional Resources

- [Cisco EVPN-VXLAN Design Guide](https://www.cisco.com/c/en/us/solutions/collateral/data-center-virtualization/application-centric-infrastructure/white-paper-c11-739942.html)
- [Catalyst Center API Documentation](https://developer.cisco.com/docs/dna-center/)
- [Ansible for Network Automation](https://docs.ansible.com/ansible/latest/network/index.html)
- [BGP EVPN Best Practices](https://www.cisco.com/c/en/us/products/collateral/switches/nexus-9000-series-switches/white-paper-c11-736015.html)

## Deployment Workflow

### Phase 1: Validation
Validate your site configuration before deployment:
```bash
ansible-playbook -i inventory/hosts.yml playbooks/main.yml \
  -e site_name=your_site --tags validation
```

### Phase 2: Complete Deployment
Execute the full deployment workflow:
```bash
ansible-playbook -i inventory/hosts.yml playbooks/main.yml \
  -e site_name=your_site
```

### Phase 3: Individual Phase Execution
Run specific phases if needed:

**Catalyst Center Setup:**
```bash
ansible-playbook -i inventory/hosts.yml playbooks/01_catalyst_center_setup.yml \
  -e site_name=your_site
```

**Site Preparation:**
```bash
ansible-playbook -i inventory/hosts.yml playbooks/02_site_preparation.yml \
  -e site_name=your_site
```

**Device Discovery:**
```bash
ansible-playbook -i inventory/hosts.yml playbooks/03_device_discovery.yml \
  -e site_name=your_site
```

**BGP Underlay:**
```bash
ansible-playbook -i inventory/hosts.yml playbooks/04_fabric_underlay.yml \
  -e site_name=your_site
```

**EVPN Overlay:**
```bash
ansible-playbook -i inventory/hosts.yml playbooks/05_evpn_overlay.yml \
  -e site_name=your_site
```

**Validation:**
```bash
ansible-playbook -i inventory/hosts.yml playbooks/06_validation.yml \
  -e site_name=your_site
```

## Monitoring and Troubleshooting

### Log Files
- Ansible execution logs: `./ansible.log`
- System logs: `/var/log/ansible-bgp-evpn.log`

### Common Issues

**Authentication Failures:**
- Verify Catalyst Center credentials
- Check network connectivity
- Ensure proper SSL certificate handling

**Device Discovery Issues:**
- Validate device IP addresses
- Check device credentials
- Verify network reachability

**Configuration Deployment Failures:**
- Review device templates
- Check for configuration conflicts
- Validate device capabilities

### Debug Commands
```bash
# Enable verbose logging
export ANSIBLE_DEBUG=1

# Run with maximum verbosity
ansible-playbook playbooks/evpn_deployment.yml -vvvv

# Check specific task output
ansible-playbook playbooks/evpn_deployment.yml --tags "sites" --step
```

### Log Files

- **Ansible Logs**: `/var/log/ansible.log`
- **Deployment Logs**: `./logs/deployment.log`
- **Validation Logs**: Output from validation scripts

## Rollback Procedures

### Automatic Rollback
The automation includes automatic rollback on failure when enabled:
```yaml
deployment:
  rollback_on_failure: true
```

### Manual Rollback
If manual rollback is needed:
```bash
ansible-playbook -i inventory/hosts.yml roles/validation/tasks/rollback.yml \
  -e site_name=your_site
```

## Best Practices

### Pre-Deployment
1. **Backup Configurations**: Always backup existing configurations
2. **Validate Input**: Run input validation before deployment
3. **Test Environment**: Test in a lab environment first
4. **Change Windows**: Deploy during maintenance windows

### During Deployment
1. **Monitor Progress**: Watch Ansible output for errors
2. **Parallel Execution**: Use parallel deployment for efficiency
3. **Staged Rollout**: Deploy in phases for large fabrics

### Post-Deployment
1. **Validation**: Run comprehensive validation tests
2. **Documentation**: Update network documentation
3. **Monitoring**: Enable fabric monitoring and alerting
4. **Backup**: Create post-deployment configuration backups

## Customization

### Adding New Sites
1. Create new site configuration file in `data/sites/`
2. Follow the existing data model structure
3. Validate configuration with schema
4. Deploy using standard workflow

### Modifying Templates
1. Edit Jinja2 templates in `templates/`
2. Test template rendering
3. Validate generated configurations
4. Deploy incrementally

### Extending Roles
1. Add new tasks to existing roles
2. Create new roles for additional functionality
3. Update main playbooks to include new tasks
4. Test thoroughly before production use

## Support and Maintenance

### Regular Maintenance
- Update Ansible collections regularly
- Review and update site configurations
- Monitor fabric health and performance
- Maintain backup and recovery procedures

### Getting Help
- Review logs for error details
- Check Cisco documentation for specific features
- Consult Ansible documentation for automation issues
- Engage with community forums for best practices

```
