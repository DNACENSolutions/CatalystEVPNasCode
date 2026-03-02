# OSPF Underlay Configuration Guide

## Overview

The **OSPF Underlay Configuration** system generates and applies OSPF routing configurations to Catalyst switches. It automatically detects existing IP addresses from running configurations and enables OSPF on all underlay interfaces while preserving the existing addressing scheme.

## Key Features

✅ **Preserves Existing IPs** - Uses current IP addresses from running configs  
✅ **OSPF Process 1** - Configures OSPF process ID 1  
✅ **Area 0** - All interfaces in OSPF area 0  
✅ **Loopback0 Router-ID** - Uses Loopback0 IP as OSPF router-id  
✅ **Point-to-Point Links** - Configures physical interfaces as point-to-point  
✅ **Automatic Backup** - Backs up configs before applying changes  
✅ **Verification** - Checks OSPF neighbors and interfaces after application  

## Files

| File | Description |
|------|-------------|
| `generate_ospf_underlay.py` | Generates OSPF configs from running configs |
| `apply_ospf_underlay.py` | PyATS script to apply OSPF configs |
| `apply_ospf_underlay_job.py` | PyATS job orchestrator |
| `run_ospf_underlay.sh` | Shell wrapper for easy execution |
| `ospf_underlay_configs/` | Directory containing generated OSPF configs |

## Quick Start

### Step 1: Generate OSPF Configurations

```bash
cd test

# Generate OSPF configs from latest device backups
python3 generate_ospf_underlay.py
```

This will:
- Read running configs from `device_configs/<latest>/running_configs/`
- Extract interface IP addresses
- Generate OSPF configurations
- Save to `ospf_underlay_configs/`

### Step 2: Apply OSPF Configurations

```bash
# Apply to all devices
./run_ospf_underlay.sh

# Apply to specific devices
./run_ospf_underlay.sh --devices TB16-Spine,TB16-SJ-Leaf-1

# Dry run (no changes)
./run_ospf_underlay.sh --dry-run
```

## Generated OSPF Configuration

For each device, the generator creates a configuration with:

### OSPF Router Configuration

```cisco
router ospf 1
 router-id 204.1.1.4
 network 204.1.1.4 0.0.0.0 area 0
 network 204.1.1.3 0.0.0.1 area 0
 network 204.1.208.1 0.0.3.255 area 0
!
```

### Interface OSPF Configuration

```cisco
interface Loopback0
 ip ospf 1 area 0
 exit
!
interface GigabitEthernet2/0/4
 ip ospf 1 area 0
 ip ospf network point-to-point
 exit
!
interface Vlan600
 ip ospf 1 area 0
 exit
!
```

## What Gets Configured

### Interfaces Included

1. **Loopback Interfaces** - All loopbacks in global routing table
2. **Physical Interfaces** - Routed interfaces (no switchport) with IP addresses
3. **VLAN Interfaces** - SVIs with IP addresses in global routing table

### Interfaces Excluded

- Interfaces in VRFs (except global routing table)
- Management interfaces (Mgmt-vrf)
- Interfaces without IP addresses
- Switchport interfaces (Layer 2)

## Usage Methods

### Method 1: Shell Wrapper (Recommended)

```bash
# Interactive with confirmation
./run_ospf_underlay.sh

# Specific devices
./run_ospf_underlay.sh -d TB16-SJ-Leaf-1,TB16-SJ-Leaf-2

# Dry run to preview changes
./run_ospf_underlay.sh --dry-run

# Custom testbed
./run_ospf_underlay.sh -t /path/to/testbed.yaml
```

### Method 2: PyATS Job

```bash
pyats run job apply_ospf_underlay_job.py \
  --testbed-file evpn_testbed.yaml \
  --devices TB16-Spine \
  --dry-run
```

### Method 3: Direct Python Script

```bash
python apply_ospf_underlay.py \
  --testbed evpn_testbed.yaml \
  --devices TB16-Fusion
```

## Configuration Details

### OSPF Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| Process ID | 1 | OSPF process identifier |
| Area | 0 | Backbone area |
| Router-ID | Loopback0 IP | Uses Loopback0 IP address |
| Network Type | Point-to-Point | For physical interfaces |

### Network Statements

The generator creates network statements for all interfaces:

- **Loopbacks**: `/32` mask (0.0.0.0 wildcard)
- **Physical Links**: Calculated from subnet mask
- **VLANs**: Calculated from subnet mask

### Wildcard Mask Calculation

Subnet masks are automatically converted to OSPF wildcard masks:

| Subnet Mask | Wildcard Mask | CIDR |
|-------------|---------------|------|
| 255.255.255.255 | 0.0.0.0 | /32 |
| 255.255.255.254 | 0.0.0.1 | /31 |
| 255.255.255.252 | 0.0.0.3 | /30 |
| 255.255.255.0 | 0.0.0.255 | /24 |
| 255.255.252.0 | 0.0.3.255 | /22 |

## Verification

After applying OSPF, the script verifies:

### 1. OSPF Process Running

```bash
show ip ospf
```

Expected: `Routing Process "ospf 1"` present

### 2. OSPF Neighbors

```bash
show ip ospf neighbor
```

Expected: Neighbors in `FULL` state

### 3. OSPF Interfaces

```bash
show ip ospf interface brief
```

Expected: Interfaces showing as `up`

### Manual Verification Commands

```bash
# Check OSPF configuration
show running-config | section router ospf

# Check OSPF neighbors
show ip ospf neighbor

# Check OSPF routes
show ip route ospf

# Check OSPF interface details
show ip ospf interface

# Check OSPF database
show ip ospf database
```

## Example Output

### Generation Output

```
======================================================================
OSPF Underlay Configuration Generator
======================================================================
Config Directory: .../running_configs
Output Directory: .../ospf_underlay_configs
======================================================================

Found 8 device configurations

Processing TB16-Spine_running.cfg...
  Found 8 interfaces in global routing table
  ✓ Generated OSPF config: TB16-Spine_ospf_underlay.cfg

Processing TB16-SJ-Leaf-1_running.cfg...
  Found 4 interfaces in global routing table
  ✓ Generated OSPF config: TB16-SJ-Leaf-1_ospf_underlay.cfg

======================================================================
Generation Summary
======================================================================
Total Devices: 8
Successful: 8
Failed: 0
```

### Application Output

```
======================================================================
Applying OSPF Underlay Configuration
======================================================================

Applying OSPF to TB16-Spine
Applying 45 configuration commands...
✓ Successfully applied OSPF to TB16-Spine

======================================================================
Verifying OSPF Configuration
======================================================================

Verifying TB16-Spine
  ✓ OSPF Process: OSPF process 1 is running
  ✓ OSPF Neighbors: 4 neighbor(s) in FULL state
  ✓ OSPF Interfaces: 8 interface(s) enabled
```

## Troubleshooting

### Issue: No config files found

**Solution:** Run device config collection first:

```bash
pyats run job collect_configs_job.py --testbed-file evpn_testbed.yaml
```

### Issue: OSPF neighbors not forming

**Possible causes:**
1. Physical connectivity issues
2. IP addressing mismatch
3. Area mismatch
4. Authentication mismatch (if configured)

**Debug commands:**

```bash
show ip ospf interface
show ip ospf neighbor
debug ip ospf adj
```

### Issue: Configuration errors during application

**Solution:** The script uses `error_pattern=[]` to continue on errors. Check logs for specific issues.

### Issue: Router-ID not set correctly

**Solution:** Ensure Loopback0 exists with an IP address in the global routing table.

## Best Practices

1. **Backup First** - Always backup configs before applying (script does this automatically)
2. **Dry Run** - Test with `--dry-run` flag first
3. **Staged Rollout** - Apply to one device first, verify, then proceed
4. **Verify Neighbors** - Check OSPF neighbors form correctly
5. **Check Routes** - Verify OSPF routes are learned

## Integration with EVPN

OSPF underlay provides the foundation for BGP EVPN overlay:

1. **OSPF** - Provides IP reachability for underlay
2. **BGP EVPN** - Runs over OSPF underlay for overlay services
3. **Loopback0** - Used for both OSPF router-id and BGP EVPN peering

### Typical Deployment Order

1. Configure physical interfaces with IP addresses
2. Apply OSPF underlay (this tool)
3. Verify OSPF neighbors and routes
4. Configure BGP EVPN overlay
5. Verify BGP EVPN peers and routes

## Advanced Usage

### Custom OSPF Process ID

Edit `generate_ospf_underlay.py`:

```python
self.ospf_process_id = 100  # Change from 1 to 100
```

### Custom OSPF Area

Edit `generate_ospf_underlay.py`:

```python
self.ospf_area = 10  # Change from 0 to 10
```

### Exclude Specific Interfaces

Modify the parsing logic in `parse_running_config()` to skip specific interfaces.

## Safety Features

- ✅ Backs up configs before applying
- ✅ Preserves existing IP addresses
- ✅ Only configures interfaces in global routing table
- ✅ Skips management interfaces
- ✅ Dry-run mode available
- ✅ Verification after application
- ✅ Detailed logging

## Rollback Procedure

If OSPF causes issues:

### Option 1: Remove OSPF Configuration

```cisco
no router ospf 1

interface Loopback0
 no ip ospf 1 area 0
 exit

interface GigabitEthernet2/0/4
 no ip ospf 1 area 0
 no ip ospf network point-to-point
 exit
```

### Option 2: Restore from Backup

```bash
# Backups are in device_configs/pre_ospf_<timestamp>/
# Use PyATS or manual restore
```

## Logging

PyATS logs are stored in:

```bash
~/.pyats/archive/<job-id>/
```

View logs:

```bash
# Find latest job
ls -lt ~/.pyats/archive/

# View log
tail -f ~/.pyats/archive/<job-id>/TaskLog.html
```

## Support

For issues:
1. Check PyATS logs for detailed error messages
2. Verify device connectivity
3. Ensure proper credentials in testbed
4. Review this README for common issues

## Example: Complete Workflow

```bash
# Step 1: Collect device configs
pyats run job collect_configs_job.py --testbed-file evpn_testbed.yaml

# Step 2: Generate OSPF configs
python3 generate_ospf_underlay.py

# Step 3: Review generated configs
ls -la ospf_underlay_configs/
cat ospf_underlay_configs/TB16-Spine_ospf_underlay.cfg

# Step 4: Dry run
./run_ospf_underlay.sh --dry-run

# Step 5: Apply to one device first
./run_ospf_underlay.sh --devices TB16-Spine

# Step 6: Verify
# SSH to device and check: show ip ospf neighbor

# Step 7: Apply to all devices
./run_ospf_underlay.sh
```

## Notes

- OSPF process ID 1 is used by default
- All interfaces are placed in area 0 (backbone)
- Physical interfaces are configured as point-to-point
- VRF interfaces are excluded (only global routing table)
- Configuration is saved automatically (`write memory`)
