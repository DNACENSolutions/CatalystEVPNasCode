#!/usr/bin/env python3
"""
Dynamic EVPN Cleanup Function
Intelligently removes BGP EVPN/VXLAN components without static config files
Handles partial cleanups gracefully
"""

import re
import logging

logger = logging.getLogger(__name__)


def cleanup_config_key(device, key_pattern):
    """
    Remove configuration blocks matching a key pattern
    Similar to the overlay cleanup helper function
    """
    try:
        cmd = f"show running-config | section {key_pattern}"
        output = device.execute(cmd, prompt_recovery=True)
        
        if not output or len(output.strip()) < 10:
            logger.info(f"No config found for pattern: {key_pattern}")
            return
        
        lines = output.split('\n')
        if lines:
            # Get the main config line
            main_line = lines[0].strip()
            if main_line and not main_line.startswith('!'):
                try:
                    device.configure(f"no {main_line}", prompt_recovery=True)
                    logger.info(f"✓ Removed: {main_line}")
                except Exception as e:
                    logger.info(f"Ignore error while removing {main_line}: {e}")
    except Exception as e:
        logger.info(f"Ignore error for pattern {key_pattern}: {e}")


def clear_device_evpn(device, remove_bgp_completely=False, preserve_mgmt_vrf=True, excluded_vlans=None):
    """
    Dynamically clean EVPN/VXLAN configuration from a device
    
    Args:
        device: PyATS device object
        remove_bgp_completely: If True, removes entire BGP process
        preserve_mgmt_vrf: If True, preserves Mgmt-vrf (default)
        excluded_vlans: List of VLAN IDs to exclude from cleanup (default: [50, 51, 52])
    
    Returns:
        1 on success, 0 on failure
    """
    
    # Default excluded VLANs (special VLANs)
    if excluded_vlans is None:
        excluded_vlans = [50, 51, 52]
    
    if not device.is_connected():
        logger.info(f"Connecting to {device.name}...")
        device.connect(log_stdout=False)
    
    logger.info(f"{'='*60}")
    logger.info(f"Starting dynamic EVPN cleanup on {device.name}")
    logger.info(f"{'='*60}")
    
    # Disable console logging to reduce noise
    try:
        device.configure("no logging console", prompt_recovery=True)
    except:
        pass
    
    # ========================================
    # Step 1: Remove BGP EVPN Address-Families
    # ========================================
    logger.info("\n[Step 1] Removing BGP EVPN address-families...")
    try:
        cmd = "show running-config | section router bgp"
        output = device.execute(cmd, prompt_recovery=True)
        
        if "router bgp" in output:
            lines = output.split('\n')
            bgp_line = None
            config_lines = []
            
            for line in lines:
                if line.startswith('router bgp'):
                    bgp_line = line.strip()
                elif 'address-family l2vpn evpn' in line:
                    config_lines.append(' no address-family l2vpn evpn')
                elif 'address-family ipv4 mvpn' in line:
                    config_lines.append(' no address-family ipv4 mvpn')
                elif re.search(r'address-family ipv4 vrf (\S+)', line):
                    vrf_match = re.search(r'address-family ipv4 vrf (\S+)', line)
                    vrf_name = vrf_match.group(1)
                    if not (preserve_mgmt_vrf and vrf_name == 'Mgmt-vrf'):
                        config_lines.append(f' no address-family ipv4 vrf {vrf_name}')
            
            if bgp_line and config_lines:
                config = bgp_line + '\n' + '\n'.join(config_lines)
                try:
                    device.configure(config, prompt_recovery=True)
                    logger.info(f"✓ Removed BGP EVPN address-families")
                except Exception as e:
                    logger.info(f"Ignore errors (already removed): {e}")
    except Exception as e:
        logger.info(f"Step 1 error (continuing): {e}")
    
    # ========================================
    # Step 2: Remove NVE Interface VNI Members
    # ========================================
    logger.info("\n[Step 2] Removing NVE interface VNI members...")
    try:
        cmd = "show running-config | section interface nve"
        output = device.execute(cmd, prompt_recovery=True)
        
        if "interface nve" in output:
            lines = output.split('\n')
            nve_line = None
            vni_commands = []
            
            for line in lines:
                if line.startswith('interface nve'):
                    nve_line = line.strip()
                elif 'member vni' in line:
                    vni_commands.append(f" no {line.strip()}")
            
            if nve_line and vni_commands:
                config = nve_line + '\n' + '\n'.join(vni_commands)
                try:
                    device.configure(config, prompt_recovery=True)
                    logger.info(f"✓ Removed NVE VNI members")
                except Exception as e:
                    logger.info(f"Ignore errors (already removed): {e}")
    except Exception as e:
        logger.info(f"Step 2 error (continuing): {e}")
    
    # ========================================
    # Step 3: Remove NVE Interfaces
    # ========================================
    logger.info("\n[Step 3] Removing NVE interfaces...")
    try:
        cmd = "show running-config | include ^interface nve"
        output = device.execute(cmd, prompt_recovery=True)
        lines = output.split('\n')
        
        for line in lines:
            if line.strip().startswith('interface nve'):
                try:
                    device.configure(f"no {line.strip()}", prompt_recovery=True)
                    logger.info(f"✓ Removed: {line.strip()}")
                except Exception as e:
                    logger.info(f"Ignore error: {e}")
    except Exception as e:
        logger.info(f"Step 3 error (continuing): {e}")
    
    # ========================================
    # Step 4: Remove EVPN Instance from VLANs
    # ========================================
    logger.info("\n[Step 4] Removing EVPN instances from VLANs...")
    try:
        cmd = "show running-config | section vlan configuration"
        output = device.execute(cmd, prompt_recovery=True)
        
        # Parse vlan configurations
        vlan_configs = re.findall(r'vlan configuration (\d+)\s+member evpn-instance (\d+) vni (\d+)', 
                                   output, re.MULTILINE)
        
        for vlan_id, instance_id, vni in vlan_configs:
            try:
                config = f"vlan configuration {vlan_id}\n no member evpn-instance {instance_id} vni {vni}"
                device.configure(config, prompt_recovery=True)
                logger.info(f"✓ Removed EVPN instance {instance_id} from VLAN {vlan_id}")
            except Exception as e:
                logger.info(f"Ignore error for VLAN {vlan_id}: {e}")
    except Exception as e:
        logger.info(f"Step 4 error (continuing): {e}")
    
    # ========================================
    # Step 5: Remove L2VPN EVPN Instances
    # ========================================
    logger.info("\n[Step 5] Removing L2VPN EVPN instances...")
    try:
        cmd = "show running-config | include ^l2vpn evpn instance"
        output = device.execute(cmd, prompt_recovery=True)
        lines = output.split('\n')
        
        for line in lines:
            if line.strip().startswith('l2vpn evpn instance'):
                try:
                    device.configure(f"no {line.strip()}", prompt_recovery=True)
                    logger.info(f"✓ Removed: {line.strip()}")
                except Exception as e:
                    logger.info(f"Ignore error: {e}")
    except Exception as e:
        logger.info(f"Step 5 error (continuing): {e}")
    
    # ========================================
    # Step 6: Remove SVI Interfaces (Vlan interfaces)
    # ========================================
    logger.info("\n[Step 6] Removing SVI interfaces...")
    try:
        cmd = "show running-config | include ^interface Vlan"
        output = device.execute(cmd, prompt_recovery=True)
        lines = output.split('\n')
        
        for line in lines:
            vlan_match = re.match(r'interface Vlan(\d+)', line.strip())
            if vlan_match:
                vlan_id = vlan_match.group(1)
                # Skip VLAN 1 (management) and special VLANs 50, 51, 52
                if vlan_id != '1' and int(vlan_id) not in excluded_vlans:
                    try:
                        device.configure(f"no interface Vlan{vlan_id}", prompt_recovery=True)
                        logger.info(f"✓ Removed: interface Vlan{vlan_id}")
                    except Exception as e:
                        logger.info(f"Ignore error for Vlan{vlan_id}: {e}")
    except Exception as e:
        logger.info(f"Step 6 error (continuing): {e}")
    
    # ========================================
    # Step 7: Remove VLAN VNI Configurations
    # ========================================
    logger.info("\n[Step 7] Removing VLAN VNI configurations...")
    try:
        cmd = "show running-config | section vlan configuration"
        output = device.execute(cmd, prompt_recovery=True)
        
        # Parse vlan configurations with member vni
        vlan_vni_configs = re.findall(r'vlan configuration (\d+)\s+member vni (\d+)', 
                                       output, re.MULTILINE)
        
        for vlan_id, vni in vlan_vni_configs:
            # Skip special VLANs 50, 51, 52
            if int(vlan_id) not in excluded_vlans:
                try:
                    config = f"vlan configuration {vlan_id}\n no member vni {vni}"
                    device.configure(config, prompt_recovery=True)
                    logger.info(f"✓ Removed VNI {vni} from VLAN {vlan_id}")
                except Exception as e:
                    logger.info(f"Ignore error for VLAN {vlan_id}: {e}")
    except Exception as e:
        logger.info(f"Step 7 error (continuing): {e}")
    
    # ========================================
    # Step 8: Remove EVPN VLANs (bulk removal)
    # ========================================
    logger.info("\n[Step 8] Removing EVPN VLANs...")
    try:
        cmd = "show vlan brief"
        output = device.execute(cmd, prompt_recovery=True)
        
        # Extract VLAN IDs (skip VLAN 1, special VLANs 50/51/52, and default VLANs)
        vlan_ids = []
        for line in output.split('\n'):
            vlan_match = re.match(r'^(\d+)\s+', line)
            if vlan_match:
                vlan_id = int(vlan_match.group(1))
                # Skip VLAN 1, special VLANs, and default VLANs 1002-1005
                if vlan_id > 1 and vlan_id < 1002 and vlan_id not in excluded_vlans:
                    vlan_ids.append(str(vlan_id))
        
        if vlan_ids:
            # Remove in chunks to avoid command length issues
            chunk_size = 50
            for i in range(0, len(vlan_ids), chunk_size):
                chunk = vlan_ids[i:i+chunk_size]
                try:
                    device.configure(f"no vlan {','.join(chunk)}", prompt_recovery=True)
                    logger.info(f"✓ Removed VLANs: {','.join(chunk)}")
                except Exception as e:
                    logger.info(f"Ignore error for VLAN chunk: {e}")
    except Exception as e:
        logger.info(f"Step 8 error (continuing): {e}")
    
    # ========================================
    # Step 9: Remove VRF Definitions
    # ========================================
    logger.info("\n[Step 9] Removing VRF definitions...")
    try:
        cmd = "show running-config | include ^vrf definition"
        output = device.execute(cmd, prompt_recovery=True)
        lines = output.split('\n')
        
        for line in lines:
            vrf_match = re.match(r'vrf definition (\S+)', line.strip())
            if vrf_match:
                vrf_name = vrf_match.group(1)
                # Skip Mgmt-vrf if preserve flag is set
                if not (preserve_mgmt_vrf and vrf_name == 'Mgmt-vrf'):
                    try:
                        device.configure(f"no vrf definition {vrf_name}", prompt_recovery=True)
                        logger.info(f"✓ Removed VRF: {vrf_name}")
                    except Exception as e:
                        logger.info(f"Ignore error for VRF {vrf_name}: {e}")
    except Exception as e:
        logger.info(f"Step 9 error (continuing): {e}")
    
    # ========================================
    # Step 10: Remove VRF Multicast Routing
    # ========================================
    logger.info("\n[Step 10] Removing VRF multicast routing...")
    try:
        cmd = "show running-config | include ^ip multicast-routing vrf"
        output = device.execute(cmd, prompt_recovery=True)
        lines = output.split('\n')
        
        for line in lines:
            if line.strip().startswith('ip multicast-routing vrf'):
                try:
                    device.configure(f"no {line.strip()}", prompt_recovery=True)
                    logger.info(f"✓ Removed: {line.strip()}")
                except Exception as e:
                    logger.info(f"Ignore error: {e}")
    except Exception as e:
        logger.info(f"Step 10 error (continuing): {e}")
    
    # ========================================
    # Step 11: Remove BGP Completely (Optional)
    # ========================================
    if remove_bgp_completely:
        logger.info("\n[Step 11] Removing BGP completely...")
        try:
            cmd = "show running-config | include ^router bgp"
            output = device.execute(cmd, prompt_recovery=True)
            
            if "router bgp" in output:
                bgp_match = re.search(r'router bgp (\d+)', output)
                if bgp_match:
                    asn = bgp_match.group(1)
                    try:
                        device.configure(f"no router bgp {asn}", prompt_recovery=True)
                        logger.info(f"✓ Removed BGP AS {asn}")
                    except Exception as e:
                        logger.info(f"Ignore error: {e}")
        except Exception as e:
            logger.info(f"Step 11 error (continuing): {e}")
    
    # ========================================
    # Step 12: Save Configuration
    # ========================================
    logger.info("\n[Step 12] Saving configuration...")
    try:
        device.execute("write memory", prompt_recovery=True)
        logger.info("✓ Configuration saved")
    except Exception as e:
        logger.info(f"Error saving config: {e}")
    
    logger.info(f"\n{'='*60}")
    logger.info(f"✓ Dynamic EVPN cleanup completed on {device.name}")
    logger.info(f"{'='*60}\n")
    
    return 1


def clear_multiple_devices_evpn(testbed, device_names=None, remove_bgp=False):
    """
    Clean EVPN from multiple devices
    
    Args:
        testbed: PyATS testbed object
        device_names: List of device names (None = all devices)
        remove_bgp: If True, removes BGP completely
    
    Returns:
        Dictionary of results {device_name: success/failure}
    """
    results = {}
    
    devices_to_clean = device_names if device_names else testbed.devices.keys()
    
    for device_name in devices_to_clean:
        if device_name not in testbed.devices:
            logger.warning(f"Device {device_name} not in testbed, skipping")
            continue
        
        device = testbed.devices[device_name]
        
        try:
            result = clear_device_evpn(device, remove_bgp_completely=remove_bgp)
            results[device_name] = 'SUCCESS' if result == 1 else 'FAILED'
        except Exception as e:
            logger.error(f"Failed to clean {device_name}: {e}")
            results[device_name] = f'FAILED: {e}'
    
    return results
