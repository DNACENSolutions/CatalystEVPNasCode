# EVPN Cleanup Configuration Fixes

## Issues Fixed

### 1. **Incomplete "no member vni" Commands**
**Problem:** Commands like `no member vni` without VNI numbers caused "% Incomplete command" errors.

**Fix:** Added specific VNI numbers to all commands:
```
# Before (WRONG)
vlan configuration 901
 no member vni

# After (CORRECT)
vlan configuration 901
 no member vni 50901
 exit
```

### 2. **EVPN Instance Removal Order**
**Problem:** Trying to remove L2VPN EVPN instances before removing them from VLANs caused:
```
% Remove EVPN instance from vlan before deletion
```

**Fix:** Added step to remove EVPN instances from VLANs first:
```
# Step 4: Remove EVPN Instance from VLANs (NEW STEP)
vlan configuration 101
 no member evpn-instance 101 vni 10101
 exit

# Step 5: Remove L2VPN EVPN Instances (AFTER removing from VLANs)
no l2vpn evpn instance 101 vlan-based
```

### 3. **NVE Interface VNI Members**
**Problem:** Deleting NVE interface without removing VNI members first.

**Fix:** Added step to remove all VNI members from NVE interface:
```
# Step 2: Remove NVE Interface VNI Members (NEW STEP)
interface nve1
 no member vni 50901 vrf red
 no member vni 50902 vrf blue
 no member vni 50903 vrf green
 no member vni 10101 mcast-group 239.190.100.101
 no member vni 10201 mcast-group 239.190.100.201
 no member vni 10401 mcast-group 239.190.100.41
 no member vni 10501 mcast-group 239.190.100.51
 exit

# Step 3: Remove NVE Interface (AFTER removing members)
no interface nve1
```

### 4. **BGP Configuration Mode**
**Problem:** Using `no router bgp 65001` inside router config mode.

**Fix:** Changed to use `exit` to leave router config mode:
```
# Before (WRONG)
router bgp 65001
 no address-family l2vpn evpn
 no router bgp 65001

# After (CORRECT)
router bgp 65001
 no address-family l2vpn evpn
 exit
!
# Later, at global config level:
no router bgp 65001
```

### 5. **Exit Commands**
**Problem:** Missing `exit` commands after configuration blocks.

**Fix:** Added `exit` after each configuration context:
```
vlan configuration 901
 no member vni 50901
 exit    # <-- Added
```

## Corrected Cleanup Order

The proper order for EVPN cleanup is now:

1. **Remove BGP EVPN Address-Families** (inside router bgp)
2. **Remove NVE Interface VNI Members** (inside interface nve1)
3. **Remove NVE Interface** (global config)
4. **Remove EVPN Instance from VLANs** (vlan configuration mode)
5. **Remove L2VPN EVPN Instances** (global config)
6. **Remove SVI Interfaces** (global config)
7. **Remove VLAN VNI Configurations** (vlan configuration mode)
8. **Remove EVPN VLANs** (global config)
9. **Remove VRF Definitions** (global config)
10. **Remove VRF Multicast Routing** (global config)
11. **Remove BGP Completely** (optional - global config)
12. **Save Configuration**

## Files Updated

All cleanup configuration files have been corrected:

- ✅ `TB16-SJ-Leaf-1_evpn_cleanup.cfg`
- ✅ `TB16-SJ-Leaf-2_evpn_cleanup.cfg`
- ✅ `TB16-SJ-Leaf-3_evpn_cleanup.cfg`
- ✅ `TB16-SJ-BORDER-1_evpn_cleanup.cfg`
- ✅ `TB16-SJ-BORDER-2_evpn_cleanup.cfg`
- ✅ `TB16-SJ-Border-3_evpn_cleanup.cfg`
- ✅ `TB16-Spine_evpn_cleanup.cfg`
- ✅ `TB16-Fusion_evpn_cleanup.cfg` (already had config t added by user)

## VNI Mappings Used

### Leaf Switches (Leaf-1, Leaf-2, Leaf-3)
- **L3 VNIs (VRF):**
  - 50901 → red VRF
  - 50902 → blue VRF
  - 50903 → green VRF

- **L2 VNIs (VLAN):**
  - 10101 → VLAN 101
  - 10201 → VLAN 201
  - 10401 → VLAN 401
  - 10501 → VLAN 501

### Border Switches (BORDER-1, BORDER-2)
- **L3 VNIs:**
  - 50902 → blue VRF
  - 50903 → green VRF

### Spine and Border-3
- **L3 VNIs:**
  - 50901 → red VRF

## Testing the Fixed Configs

Now you can run the cleanup successfully:

```bash
cd test

# Test with dry-run first
pyats run job apply_evpn_cleanup_job.py \
  --testbed-file evpn_testbed.yaml \
  --dry-run

# Apply to all devices
pyats run job apply_evpn_cleanup_job.py \
  --testbed-file evpn_testbed.yaml
```

## Expected Results

With these fixes, the cleanup should now:
- ✅ Remove all VNI members from NVE interface
- ✅ Remove EVPN instances from VLANs
- ✅ Remove L2VPN EVPN instances
- ✅ Remove all EVPN-related configurations
- ✅ Complete without "% Incomplete command" errors
- ✅ Complete without "Remove EVPN instance from vlan" errors

## Important Notes

1. **BGP Removal:** The configs now include `no router bgp 65001` at the end. If you want to preserve BGP for underlay routing, comment out or remove this line from all cleanup configs.

2. **Order Matters:** The sequence of removal is critical. Don't change the order of steps.

3. **Exit Commands:** All configuration contexts now properly exit before moving to the next step.

---
**Date:** 2026-02-09  
**Fixed By:** Cascade AI Assistant  
**Status:** Ready for deployment
