# Dynamic EVPN Cleanup Guide

## Overview

The **Dynamic EVPN Cleanup** system intelligently removes BGP EVPN/VXLAN components from Catalyst switches without requiring static configuration files. It automatically detects and removes EVPN components, handles partial cleanups gracefully, and continues even when some items have already been removed.

## Key Advantages

✅ **No Static Config Files** - Dynamically detects what needs to be removed  
✅ **Handles Partial Cleanups** - Works even if some components already removed  
✅ **Continues on Errors** - Ignores "does not exist" errors and keeps going  
✅ **Intelligent Detection** - Parses running config to find EVPN components  
✅ **Preserves Underlay** - Keeps ISIS/OSPF routing intact  
✅ **Preserves Management** - Keeps Mgmt-vrf and VLAN 1  

## Files

| File | Description |
|------|-------------|
| `dynamic_evpn_cleanup.py` | Core cleanup functions with intelligent detection |
| `apply_dynamic_evpn_cleanup.py` | PyATS test script for cleanup execution |
| `apply_dynamic_evpn_cleanup_job.py` | PyATS job orchestrator |
| `run_dynamic_evpn_cleanup.sh` | Shell wrapper for easy execution |

## Quick Start

### Basic Usage (All Devices)

```bash
cd test
./run_dynamic_evpn_cleanup.sh
```

### Specific Devices

```bash
./run_dynamic_evpn_cleanup.sh --devices TB16-Fusion,TB16-Spine
```

### Remove BGP Completely

```bash
./run_dynamic_evpn_cleanup.sh --remove-bgp
```

## What Gets Removed

The dynamic cleanup removes the following EVPN/VXLAN components:

### Step 1: BGP EVPN Address-Families
- `address-family l2vpn evpn`
- `address-family ipv4 mvpn`
- `address-family ipv4 vrf <vrf-name>` (except Mgmt-vrf)

### Step 2: NVE Interface VNI Members
- `member vni <vni> vrf <vrf-name>`
- `member vni <vni> mcast-group <ip>`

### Step 3: NVE Interfaces
- `interface nve1`

### Step 4: EVPN Instance from VLANs
- `member evpn-instance <id> vni <vni>` (from vlan configuration)

### Step 5: L2VPN EVPN Instances
- `l2vpn evpn instance <id> vlan-based`

### Step 6: SVI Interfaces
- `interface Vlan<id>` (except VLAN 1)

### Step 7: VLAN VNI Configurations
- `member vni <vni>` (from vlan configuration)

### Step 8: EVPN VLANs
- All VLANs except VLAN 1 and default VLANs (1002-1005)

### Step 9: VRF Definitions
- `vrf definition <name>` (except Mgmt-vrf)

### Step 10: VRF Multicast Routing
- `ip multicast-routing vrf <name>`

### Step 11: BGP (Optional)
- `router bgp <asn>` (only if `--remove-bgp` flag used)

## What Gets Preserved

✅ **Underlay Routing** - ISIS and OSPF configurations  
✅ **Physical Interfaces** - All physical interface configs  
✅ **Management** - Mgmt-vrf and VLAN 1  
✅ **Basic Config** - Hostname, AAA, logging, etc.  
✅ **BGP** - Preserved by default (only EVPN removed)  

## Usage Methods

### Method 1: Shell Wrapper (Recommended)

```bash
# Interactive with confirmation
./run_dynamic_evpn_cleanup.sh

# Specific devices
./run_dynamic_evpn_cleanup.sh -d TB16-SJ-Leaf-1,TB16-SJ-Leaf-2

# Remove BGP completely
./run_dynamic_evpn_cleanup.sh --remove-bgp

# Custom testbed
./run_dynamic_evpn_cleanup.sh -t /path/to/testbed.yaml
```

### Method 2: PyATS Job

```bash
pyats run job apply_dynamic_evpn_cleanup_job.py \
  --testbed-file evpn_testbed.yaml \
  --devices TB16-Fusion \
  --remove-bgp
```

### Method 3: Direct Python Script

```bash
python apply_dynamic_evpn_cleanup.py \
  --testbed evpn_testbed.yaml \
  --devices TB16-Spine
```

### Method 4: Python Function (Programmatic)

```python
from dynamic_evpn_cleanup import clear_device_evpn, clear_multiple_devices_evpn
from pyats.topology import loader

# Load testbed
testbed = loader.load('evpn_testbed.yaml')

# Clean single device
device = testbed.devices['TB16-Fusion']
device.connect()
result = clear_device_evpn(device, remove_bgp_completely=False)

# Clean multiple devices
results = clear_multiple_devices_evpn(
    testbed, 
    device_names=['TB16-Spine', 'TB16-Fusion'],
    remove_bgp=False
)
```

## Error Handling

The dynamic cleanup is designed to handle errors gracefully:

### Expected Errors (Ignored)

```
% VRF DEFAULT_VN does not exist.
% Invalid input detected at '^' marker.
Interface not found
VLAN does not exist
```

These errors occur when:
- Running cleanup multiple times
- Components already manually removed
- Partial cleanup already performed

The script **continues** and completes all other cleanup steps.

### Actual Errors (Reported)

- Connection failures
- Authentication issues
- Device unreachable
- Command syntax errors

## Verification

After cleanup, the script verifies:

1. **L2VPN EVPN** - No l2vpn evpn instances remain
2. **NVE Interface** - No NVE interfaces remain
3. **BGP EVPN AF** - No EVPN address-families remain

Manual verification commands:

```bash
# Check for any EVPN components
show running-config | include evpn
show running-config | include nve
show running-config | section l2vpn

# Verify underlay still works
show ip route isis
show ip route ospf
show isis neighbors
show ip ospf neighbor
```

## Comparison: Static vs Dynamic Cleanup

| Feature | Static Cleanup | Dynamic Cleanup |
|---------|---------------|-----------------|
| Config Files Required | ✅ Yes | ❌ No |
| Handles Partial Cleanup | ❌ Fails | ✅ Continues |
| Errors on Missing Items | ✅ Yes | ❌ No |
| Requires Regeneration | ✅ Yes | ❌ No |
| Idempotent | ❌ No | ✅ Yes |
| Works After Manual Changes | ❌ No | ✅ Yes |

## Troubleshooting

### Issue: Script stops on first error

**Solution:** The dynamic cleanup uses `prompt_recovery=True` and ignores common errors. If it still stops, check device connectivity.

### Issue: Some components not removed

**Solution:** Run the cleanup again - it's idempotent and will clean remaining items.

### Issue: Connection timeout

**Solution:** 
```bash
# Increase timeout in testbed.yaml
devices:
  TB16-Fusion:
    connections:
      a:
        timeout: 120  # Increase from default
```

### Issue: BGP removed when not wanted

**Solution:** Don't use `--remove-bgp` flag. By default, only EVPN address-families are removed.

## Advanced Usage

### Custom Cleanup Function

```python
from dynamic_evpn_cleanup import clear_device_evpn

# Custom cleanup with options
result = clear_device_evpn(
    device,
    remove_bgp_completely=False,  # Preserve BGP
    preserve_mgmt_vrf=True         # Keep Mgmt-vrf
)
```

### Selective Device Cleanup

```python
from dynamic_evpn_cleanup import clear_multiple_devices_evpn

# Clean only leaf switches
leaf_devices = ['TB16-SJ-Leaf-1', 'TB16-SJ-Leaf-2', 'TB16-SJ-Leaf-3']
results = clear_multiple_devices_evpn(testbed, device_names=leaf_devices)
```

### Integration with Other Scripts

```python
# In your automation script
from dynamic_evpn_cleanup import clear_device_evpn

def my_cleanup_workflow(device):
    # Pre-cleanup tasks
    backup_config(device)
    
    # Dynamic EVPN cleanup
    clear_device_evpn(device)
    
    # Post-cleanup tasks
    verify_underlay(device)
    apply_new_config(device)
```

## Best Practices

1. **Always backup first** - The script saves config automatically, but manual backup recommended
2. **Verify underlay** - Check ISIS/OSPF neighbors after cleanup
3. **Run verification** - Use built-in verification or manual checks
4. **Test on one device** - Before cleaning entire fabric
5. **Use --devices flag** - For targeted cleanup during testing

## Safety Features

- ✅ Preserves Mgmt-vrf by default
- ✅ Skips VLAN 1 (management VLAN)
- ✅ Saves configuration after cleanup
- ✅ Continues on errors (doesn't leave partial state)
- ✅ Logs all actions for audit trail
- ✅ Requires confirmation before execution

## Logging

Logs are stored in PyATS archive directory:

```bash
# View latest log
ls -lt ~/.pyats/archive/
tail -f ~/.pyats/archive/<job-id>/TaskLog.html
```

## Support

For issues or questions:
1. Check PyATS logs for detailed error messages
2. Verify device connectivity
3. Ensure proper credentials in testbed
4. Review this README for common issues

## Example Output

```
==========================================================
Starting dynamic EVPN cleanup on TB16-Fusion
==========================================================

[Step 1] Removing BGP EVPN address-families...
✓ Removed BGP EVPN address-families

[Step 2] Removing NVE interface VNI members...
✓ Removed NVE VNI members

[Step 3] Removing NVE interfaces...
✓ Removed: interface nve1

[Step 4] Removing EVPN instances from VLANs...
✓ Removed EVPN instance 101 from VLAN 101
✓ Removed EVPN instance 201 from VLAN 201

[Step 5] Removing L2VPN EVPN instances...
✓ Removed: l2vpn evpn instance 101 vlan-based
✓ Removed: l2vpn evpn instance 201 vlan-based

[Step 6] Removing SVI interfaces...
✓ Removed: interface Vlan101
✓ Removed: interface Vlan201

[Step 7] Removing VLAN VNI configurations...
✓ Removed VNI 50901 from VLAN 901
✓ Removed VNI 50902 from VLAN 902

[Step 8] Removing EVPN VLANs...
✓ Removed VLANs: 101,201,401,501,901,902,903

[Step 9] Removing VRF definitions...
✓ Removed VRF: red
✓ Removed VRF: blue
✓ Removed VRF: green

[Step 10] Removing VRF multicast routing...
✓ Removed: ip multicast-routing vrf red
✓ Removed: ip multicast-routing vrf blue

[Step 12] Saving configuration...
✓ Configuration saved

==========================================================
✓ Dynamic EVPN cleanup completed on TB16-Fusion
==========================================================
```
