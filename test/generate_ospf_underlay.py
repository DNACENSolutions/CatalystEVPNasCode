#!/usr/bin/env python3
"""
OSPF Underlay Configuration Generator
Generates OSPF configurations for devices with router-id 1
Preserves existing IP addresses from running configs
"""

import re
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Tuple


class OSPFUnderlayGenerator:
    """Generate OSPF underlay configurations from running configs"""
    
    def __init__(self, config_dir: str, output_dir: str):
        self.config_dir = Path(config_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # OSPF process ID
        self.ospf_process_id = 1
        self.ospf_area = 0
        
    def parse_running_config(self, config_file: Path) -> Dict:
        """Parse running config and extract interface information"""
        
        with open(config_file, 'r') as f:
            lines = f.readlines()
        
        components = {
            'hostname': None,
            'loopback_interfaces': [],
            'physical_interfaces': [],
            'vlan_interfaces': []
        }
        
        i = 0
        while i < len(lines):
            line = lines[i].rstrip()
            
            # Extract hostname
            if line.startswith('hostname '):
                components['hostname'] = line.split()[1]
            
            # Loopback interfaces
            elif line.startswith('interface Loopback'):
                match = re.match(r'interface Loopback(\d+)', line)
                if match:
                    loopback_id = match.group(1)
                    loopback_block = {'id': loopback_id, 'lines': [line]}
                    ip_address = None
                    subnet_mask = None
                    description = None
                    vrf = None
                    
                    i += 1
                    while i < len(lines) and lines[i].startswith((' ', '!')):
                        if lines[i].strip() == '!':
                            break
                        loopback_line = lines[i].rstrip()
                        loopback_block['lines'].append(loopback_line)
                        
                        # Extract IP address
                        if ' ip address ' in loopback_line:
                            ip_match = re.search(r'ip address (\S+) (\S+)', loopback_line)
                            if ip_match:
                                ip_address = ip_match.group(1)
                                subnet_mask = ip_match.group(2)
                        
                        # Extract description
                        if ' description ' in loopback_line:
                            desc_match = re.search(r'description (.+)', loopback_line)
                            if desc_match:
                                description = desc_match.group(1).strip()
                        
                        # Check for VRF
                        if ' vrf forwarding ' in loopback_line:
                            vrf_match = re.search(r'vrf forwarding (\S+)', loopback_line)
                            if vrf_match:
                                vrf = vrf_match.group(1)
                        
                        i += 1
                    
                    loopback_block['ip_address'] = ip_address
                    loopback_block['subnet_mask'] = subnet_mask
                    loopback_block['description'] = description
                    loopback_block['vrf'] = vrf
                    components['loopback_interfaces'].append(loopback_block)
                    continue
            
            # Physical interfaces (GigabitEthernet, TenGigabitEthernet, etc.)
            elif re.match(r'interface (GigabitEthernet|TenGigabitEthernet|FortyGigabitEthernet|TwentyFiveGigE)', line):
                match = re.match(r'interface (\S+)', line)
                if match:
                    intf_name = match.group(1)
                    intf_block = {'name': intf_name, 'lines': [line]}
                    ip_address = None
                    subnet_mask = None
                    description = None
                    vrf = None
                    is_routed = False
                    
                    i += 1
                    while i < len(lines) and lines[i].startswith((' ', '!')):
                        if lines[i].strip() == '!':
                            break
                        intf_line = lines[i].rstrip()
                        intf_block['lines'].append(intf_line)
                        
                        # Check if routed interface
                        if ' no switchport' in intf_line:
                            is_routed = True
                        
                        # Extract IP address
                        if ' ip address ' in intf_line and 'dhcp' not in intf_line:
                            ip_match = re.search(r'ip address (\S+) (\S+)', intf_line)
                            if ip_match:
                                ip_address = ip_match.group(1)
                                subnet_mask = ip_match.group(2)
                        
                        # Extract description
                        if ' description ' in intf_line:
                            desc_match = re.search(r'description (.+)', intf_line)
                            if desc_match:
                                description = desc_match.group(1).strip()
                        
                        # Check for VRF
                        if ' vrf forwarding ' in intf_line:
                            vrf_match = re.search(r'vrf forwarding (\S+)', intf_line)
                            if vrf_match:
                                vrf = vrf_match.group(1)
                        
                        i += 1
                    
                    intf_block['ip_address'] = ip_address
                    intf_block['subnet_mask'] = subnet_mask
                    intf_block['description'] = description
                    intf_block['vrf'] = vrf
                    intf_block['is_routed'] = is_routed
                    
                    # Only add if it has an IP address and is routed
                    if ip_address and is_routed:
                        components['physical_interfaces'].append(intf_block)
                    continue
            
            # VLAN interfaces
            elif line.startswith('interface Vlan'):
                match = re.match(r'interface Vlan(\d+)', line)
                if match:
                    vlan_id = match.group(1)
                    vlan_block = {'id': vlan_id, 'lines': [line]}
                    ip_address = None
                    subnet_mask = None
                    description = None
                    vrf = None
                    
                    i += 1
                    while i < len(lines) and lines[i].startswith((' ', '!')):
                        if lines[i].strip() == '!':
                            break
                        vlan_line = lines[i].rstrip()
                        vlan_block['lines'].append(vlan_line)
                        
                        # Extract IP address
                        if ' ip address ' in vlan_line and 'dhcp' not in vlan_line:
                            ip_match = re.search(r'ip address (\S+) (\S+)', vlan_line)
                            if ip_match:
                                ip_address = ip_match.group(1)
                                subnet_mask = ip_match.group(2)
                        
                        # Extract description
                        if ' description ' in vlan_line:
                            desc_match = re.search(r'description (.+)', vlan_line)
                            if desc_match:
                                description = desc_match.group(1).strip()
                        
                        # Check for VRF
                        if ' vrf forwarding ' in vlan_line:
                            vrf_match = re.search(r'vrf forwarding (\S+)', vlan_line)
                            if vrf_match:
                                vrf = vrf_match.group(1)
                        
                        i += 1
                    
                    vlan_block['ip_address'] = ip_address
                    vlan_block['subnet_mask'] = subnet_mask
                    vlan_block['description'] = description
                    vlan_block['vrf'] = vrf
                    
                    # Only add if it has an IP address
                    if ip_address:
                        components['vlan_interfaces'].append(vlan_block)
                    continue
            
            i += 1
        
        return components
    
    def generate_ospf_config(self, components: Dict) -> str:
        """Generate OSPF configuration"""
        
        config_lines = []
        
        # Header
        config_lines.append("!")
        config_lines.append(f"! OSPF Underlay Configuration for {components['hostname']}")
        config_lines.append(f"! Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        config_lines.append("!")
        config_lines.append("! This configuration enables OSPF routing on underlay interfaces")
        config_lines.append("! - OSPF Process ID: 1")
        config_lines.append("! - OSPF Area: 0")
        config_lines.append("! - Preserves existing IP addresses")
        config_lines.append("!")
        config_lines.append("")
        
        # Find Loopback0 for router-id
        loopback0_ip = None
        for loopback in components['loopback_interfaces']:
            if loopback['id'] == '0' and loopback['ip_address'] and not loopback['vrf']:
                loopback0_ip = loopback['ip_address']
                break
        
        # OSPF router configuration
        config_lines.append("! ========================================")
        config_lines.append("! OSPF Router Configuration")
        config_lines.append("! ========================================")
        config_lines.append("!")
        config_lines.append(f"router ospf {self.ospf_process_id}")
        
        if loopback0_ip:
            config_lines.append(f" router-id {loopback0_ip}")
        
        # Add networks for all interfaces in global routing table
        networks_added = set()
        
        # Add Loopback interfaces
        for loopback in components['loopback_interfaces']:
            if loopback['ip_address'] and not loopback['vrf']:
                # For loopbacks, use /32
                config_lines.append(f" network {loopback['ip_address']} 0.0.0.0 area {self.ospf_area}")
                networks_added.add(loopback['ip_address'])
        
        # Add physical interfaces
        for intf in components['physical_interfaces']:
            if intf['ip_address'] and not intf['vrf']:
                # Calculate wildcard mask from subnet mask
                wildcard = self._subnet_to_wildcard(intf['subnet_mask'])
                config_lines.append(f" network {intf['ip_address']} {wildcard} area {self.ospf_area}")
                networks_added.add(intf['ip_address'])
        
        # Add VLAN interfaces
        for vlan in components['vlan_interfaces']:
            if vlan['ip_address'] and not vlan['vrf']:
                # Calculate wildcard mask from subnet mask
                wildcard = self._subnet_to_wildcard(vlan['subnet_mask'])
                config_lines.append(f" network {vlan['ip_address']} {wildcard} area {self.ospf_area}")
                networks_added.add(vlan['ip_address'])
        
        config_lines.append("!")
        config_lines.append("")
        
        # Interface-specific OSPF configuration
        config_lines.append("! ========================================")
        config_lines.append("! Interface OSPF Configuration")
        config_lines.append("! ========================================")
        config_lines.append("!")
        
        # Configure Loopback interfaces
        for loopback in components['loopback_interfaces']:
            if loopback['ip_address'] and not loopback['vrf']:
                config_lines.append(f"interface Loopback{loopback['id']}")
                config_lines.append(f" ip ospf {self.ospf_process_id} area {self.ospf_area}")
                config_lines.append(" exit")
                config_lines.append("!")
        
        # Configure physical interfaces
        for intf in components['physical_interfaces']:
            if intf['ip_address'] and not intf['vrf']:
                config_lines.append(f"interface {intf['name']}")
                config_lines.append(f" ip ospf {self.ospf_process_id} area {self.ospf_area}")
                config_lines.append(" ip ospf network point-to-point")
                config_lines.append(" exit")
                config_lines.append("!")
        
        # Configure VLAN interfaces
        for vlan in components['vlan_interfaces']:
            if vlan['ip_address'] and not vlan['vrf']:
                config_lines.append(f"interface Vlan{vlan['id']}")
                config_lines.append(f" ip ospf {self.ospf_process_id} area {self.ospf_area}")
                config_lines.append(" exit")
                config_lines.append("!")
        
        # Save configuration
        config_lines.append("! ========================================")
        config_lines.append("! Save Configuration")
        config_lines.append("! ========================================")
        config_lines.append("!")
        config_lines.append("end")
        config_lines.append("write memory")
        config_lines.append("!")
        
        return '\n'.join(config_lines)
    
    def _subnet_to_wildcard(self, subnet_mask: str) -> str:
        """Convert subnet mask to wildcard mask"""
        try:
            octets = subnet_mask.split('.')
            wildcard_octets = [str(255 - int(octet)) for octet in octets]
            return '.'.join(wildcard_octets)
        except:
            return '0.0.0.255'  # Default wildcard for /24
    
    def process_device(self, config_file: Path) -> Tuple[str, str]:
        """Process a single device configuration"""
        
        print(f"\nProcessing {config_file.name}...")
        
        # Parse running config
        components = self.parse_running_config(config_file)
        
        if not components['hostname']:
            print(f"  ✗ Could not extract hostname from {config_file.name}")
            return None, None
        
        hostname = components['hostname']
        
        # Count interfaces
        global_intfs = sum(1 for l in components['loopback_interfaces'] if l['ip_address'] and not l['vrf'])
        global_intfs += sum(1 for p in components['physical_interfaces'] if p['ip_address'] and not p['vrf'])
        global_intfs += sum(1 for v in components['vlan_interfaces'] if v['ip_address'] and not v['vrf'])
        
        print(f"  Found {global_intfs} interfaces in global routing table")
        
        # Generate OSPF config
        ospf_config = self.generate_ospf_config(components)
        
        # Write to file
        output_file = self.output_dir / f"{hostname}_ospf_underlay.cfg"
        with open(output_file, 'w') as f:
            f.write(ospf_config)
        
        print(f"  ✓ Generated OSPF config: {output_file.name}")
        
        return hostname, str(output_file)
    
    def generate_all(self):
        """Generate OSPF configs for all devices"""
        
        print("="*70)
        print("OSPF Underlay Configuration Generator")
        print("="*70)
        print(f"Config Directory: {self.config_dir}")
        print(f"Output Directory: {self.output_dir}")
        print("="*70)
        
        # Find all running config files
        config_files = list(self.config_dir.glob("*_running.cfg"))
        
        if not config_files:
            print("\n✗ No running config files found!")
            print(f"  Looking for: {self.config_dir}/*_running.cfg")
            return
        
        print(f"\nFound {len(config_files)} device configurations")
        
        # Process each device
        results = []
        for config_file in sorted(config_files):
            hostname, output_file = self.process_device(config_file)
            if hostname:
                results.append((hostname, output_file))
        
        # Summary
        print("\n" + "="*70)
        print("Generation Summary")
        print("="*70)
        print(f"Total Devices: {len(config_files)}")
        print(f"Successful: {len(results)}")
        print(f"Failed: {len(config_files) - len(results)}")
        
        if results:
            print("\n✓ Generated OSPF configurations:")
            for hostname, output_file in results:
                print(f"  - {hostname}: {Path(output_file).name}")
        
        print("\n" + "="*70)
        print(f"OSPF configs saved to: {self.output_dir}")
        print("="*70)


def main():
    """Main function"""
    
    # Default directories
    script_dir = Path(__file__).parent
    
    # Find the most recent device config directory
    device_configs_dir = script_dir / "device_configs"
    
    if not device_configs_dir.exists():
        print(f"✗ Device configs directory not found: {device_configs_dir}")
        sys.exit(1)
    
    # Get the most recent backup directory (exclude pre_cleanup directories)
    backup_dirs = sorted([d for d in device_configs_dir.iterdir() 
                         if d.is_dir() and not d.name.startswith('pre_cleanup')], 
                        reverse=True)
    
    if not backup_dirs:
        print(f"✗ No backup directories found in {device_configs_dir}")
        sys.exit(1)
    
    latest_backup = backup_dirs[0]
    config_dir = latest_backup / "running_configs"
    
    print(f"Using config directory: {latest_backup.name}")
    
    if not config_dir.exists():
        print(f"✗ Running configs directory not found: {config_dir}")
        sys.exit(1)
    
    # Output directory
    output_dir = script_dir / "ospf_underlay_configs"
    
    # Generate OSPF configs
    generator = OSPFUnderlayGenerator(str(config_dir), str(output_dir))
    generator.generate_all()


if __name__ == '__main__':
    main()
