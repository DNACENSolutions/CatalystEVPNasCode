#!/usr/bin/env python3
"""
BGP EVPN Cleanup Configuration Generator

This script analyzes device running configurations and generates cleanup
configurations to remove BGP EVPN/VXLAN components while preserving:
- Basic device configuration (hostname, management, AAA, etc.)
- ISIS routing protocol
- OSPF routing protocol
- Physical interface configurations
- Management VRF

Author: Auto-generated for EVPN testbed cleanup
"""

import re
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Tuple


class EVPNCleanupGenerator:
    """Generate EVPN cleanup configurations from running configs"""
    
    def __init__(self, config_dir: str, output_dir: str):
        self.config_dir = Path(config_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Components to remove
        self.evpn_vrfs = set()
        self.evpn_vlans = set()
        self.evpn_instances = set()
        self.nve_interfaces = set()
        
        # Special VLANs to exclude from cleanup
        self.excluded_vlans = {'50', '51', '52'}
        
    def parse_running_config(self, config_file: Path) -> Dict:
        """Parse running config and identify EVPN components"""
        
        with open(config_file, 'r') as f:
            lines = f.readlines()
        
        components = {
            'vrfs': [],
            'vlans': [],
            'vlan_configs': [],
            'l2vpn_instances': [],
            'nve_interfaces': [],
            'nve_vni_members': [],  # VNI members from NVE interface
            'bgp_evpn': False,
            'svi_interfaces': [],
            'hostname': None
        }
        
        i = 0
        while i < len(lines):
            line = lines[i].rstrip()
            
            # Extract hostname
            if line.startswith('hostname '):
                components['hostname'] = line.split()[1]
            
            # VRF definitions (exclude Mgmt-vrf)
            elif line.startswith('vrf definition '):
                vrf_name = line.split()[2]
                if vrf_name != 'Mgmt-vrf':
                    vrf_block = [line]
                    i += 1
                    while i < len(lines) and lines[i].startswith((' ', '!')):
                        if lines[i].strip() == '!':
                            break
                        vrf_block.append(lines[i].rstrip())
                        i += 1
                    components['vrfs'].append({
                        'name': vrf_name,
                        'config': vrf_block
                    })
                    continue
            
            # L2VPN EVPN instances
            elif line.startswith('l2vpn evpn instance '):
                match = re.match(r'l2vpn evpn instance (\d+)', line)
                if match:
                    instance_id = match.group(1)
                    instance_block = [line]
                    i += 1
                    while i < len(lines) and lines[i].startswith((' ', '!')):
                        if lines[i].strip() == '!':
                            break
                        instance_block.append(lines[i].rstrip())
                        i += 1
                    components['l2vpn_instances'].append({
                        'id': instance_id,
                        'config': instance_block
                    })
                    continue
            
            # VLAN configuration (member vni)
            elif line.startswith('vlan configuration '):
                match = re.match(r'vlan configuration (\d+)', line)
                if match:
                    vlan_id = match.group(1)
                    vlan_cfg_block = [line]
                    vni_number = None
                    evpn_instance = None
                    i += 1
                    while i < len(lines) and lines[i].startswith((' ', '!')):
                        if lines[i].strip() == '!':
                            break
                        cfg_line = lines[i].rstrip()
                        vlan_cfg_block.append(cfg_line)
                        # Extract VNI number from member vni
                        if 'member vni' in cfg_line and 'evpn-instance' not in cfg_line:
                            vni_match = re.search(r'member vni (\d+)', cfg_line)
                            if vni_match:
                                vni_number = vni_match.group(1)
                        # Extract EVPN instance mapping
                        if 'member evpn-instance' in cfg_line:
                            evpn_match = re.search(r'member evpn-instance (\d+) vni (\d+)', cfg_line)
                            if evpn_match:
                                evpn_instance = {'instance_id': evpn_match.group(1), 'vni': evpn_match.group(2)}
                        i += 1
                    components['vlan_configs'].append({
                        'id': vlan_id,
                        'config': vlan_cfg_block,
                        'vni': vni_number,
                        'evpn_instance': evpn_instance
                    })
                    continue
            
            # VLAN definitions
            elif re.match(r'^vlan \d+', line):
                match = re.match(r'^vlan (\d+)', line)
                if match:
                    vlan_id = match.group(1)
                    vlan_block = [line]
                    i += 1
                    while i < len(lines) and lines[i].startswith((' ', '!')):
                        if lines[i].strip() == '!':
                            break
                        vlan_block.append(lines[i].rstrip())
                        i += 1
                    components['vlans'].append({
                        'id': vlan_id,
                        'config': vlan_block
                    })
                    continue
            
            # NVE interfaces
            elif line.startswith('interface nve'):
                nve_name = line.split()[1]
                nve_block = [line]
                i += 1
                while i < len(lines) and lines[i].startswith((' ', '!')):
                    if lines[i].strip() == '!':
                        break
                    nve_line = lines[i].rstrip()
                    nve_block.append(nve_line)
                    # Extract member vni commands
                    if 'member vni' in nve_line:
                        components['nve_vni_members'].append(nve_line.strip())
                    i += 1
                components['nve_interfaces'].append({
                    'name': nve_name,
                    'config': nve_block
                })
                continue
            
            # SVI interfaces (interface Vlan)
            elif line.startswith('interface Vlan'):
                match = re.match(r'interface Vlan(\d+)', line)
                if match:
                    vlan_id = match.group(1)
                    svi_block = [line]
                    i += 1
                    while i < len(lines) and lines[i].startswith((' ', '!')):
                        if lines[i].strip() == '!':
                            break
                        svi_block.append(lines[i].rstrip())
                        i += 1
                    components['svi_interfaces'].append({
                        'id': vlan_id,
                        'config': svi_block
                    })
                    continue
            
            # BGP configuration
            elif line.startswith('router bgp '):
                # Check if it has EVPN address-family
                bgp_block = [line]
                i += 1
                while i < len(lines) and lines[i].startswith((' ', '!')):
                    if lines[i].strip() == '!':
                        break
                    bgp_block.append(lines[i].rstrip())
                    if 'address-family l2vpn evpn' in lines[i]:
                        components['bgp_evpn'] = True
                    i += 1
                continue
            
            i += 1
        
        return components
    
    def generate_cleanup_config(self, components: Dict, device_name: str) -> str:
        """Generate cleanup configuration commands"""
        
        cleanup_lines = []
        cleanup_lines.append(f"!")
        cleanup_lines.append(f"! BGP EVPN Cleanup Configuration for {device_name}")
        cleanup_lines.append(f"! Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        cleanup_lines.append(f"!")
        cleanup_lines.append(f"! This configuration removes BGP EVPN/VXLAN components while preserving:")
        cleanup_lines.append(f"!   - Basic device configuration")
        cleanup_lines.append(f"!   - ISIS routing protocol")
        cleanup_lines.append(f"!   - OSPF routing protocol")
        cleanup_lines.append(f"!   - Physical interfaces")
        cleanup_lines.append(f"!   - Management VRF")
        cleanup_lines.append(f"!")
        cleanup_lines.append(f"! IMPORTANT: Review this configuration before applying!")
        cleanup_lines.append(f"!")
        cleanup_lines.append(f"")
        
        # Step 1: Remove BGP EVPN address-family and VRF configurations
        if components['bgp_evpn'] or components['vrfs']:
            cleanup_lines.append("! ========================================")
            cleanup_lines.append("! Step 1: Remove BGP EVPN Address-Families")
            cleanup_lines.append("! ========================================")
            cleanup_lines.append("!")
            cleanup_lines.append("router bgp 65001")
            
            # Remove L2VPN EVPN address-family
            cleanup_lines.append(" no address-family l2vpn evpn")
            
            # Remove MVPN address-family
            cleanup_lines.append(" no address-family ipv4 mvpn")
            
            # Remove VRF address-families
            for vrf in components['vrfs']:
                cleanup_lines.append(f" no address-family ipv4 vrf {vrf['name']}")
            
            cleanup_lines.append(" exit")
            cleanup_lines.append("!")
            cleanup_lines.append("")
        
        # Step 2: Remove NVE Interface VNI Members
        if components['nve_vni_members']:
            cleanup_lines.append("! ========================================")
            cleanup_lines.append("! Step 2: Remove NVE Interface VNI Members")
            cleanup_lines.append("! ========================================")
            cleanup_lines.append("!")
            if components['nve_interfaces']:
                cleanup_lines.append(f"interface {components['nve_interfaces'][0]['name']}")
                for vni_member in components['nve_vni_members']:
                    cleanup_lines.append(f" no {vni_member}")
                cleanup_lines.append(" exit")
            cleanup_lines.append("!")
            cleanup_lines.append("")
        
        # Step 3: Remove NVE interfaces
        if components['nve_interfaces']:
            cleanup_lines.append("! ========================================")
            cleanup_lines.append("! Step 3: Remove NVE Interface")
            cleanup_lines.append("! ========================================")
            cleanup_lines.append("!")
            for nve in components['nve_interfaces']:
                cleanup_lines.append(f"no interface {nve['name']}")
            cleanup_lines.append("!")
            cleanup_lines.append("")
        
        # Step 4: Remove EVPN Instance from VLANs
        evpn_vlan_configs = [vc for vc in components['vlan_configs'] if vc.get('evpn_instance')]
        if evpn_vlan_configs:
            cleanup_lines.append("! ========================================")
            cleanup_lines.append("! Step 4: Remove EVPN Instance from VLANs")
            cleanup_lines.append("! ========================================")
            cleanup_lines.append("!")
            for vlan_cfg in evpn_vlan_configs:
                cleanup_lines.append(f"vlan configuration {vlan_cfg['id']}")
                evpn = vlan_cfg['evpn_instance']
                cleanup_lines.append(f" no member evpn-instance {evpn['instance_id']} vni {evpn['vni']}")
                cleanup_lines.append(" exit")
            cleanup_lines.append("!")
            cleanup_lines.append("")
        
        # Step 5: Remove L2VPN EVPN instances
        if components['l2vpn_instances']:
            cleanup_lines.append("! ========================================")
            cleanup_lines.append("! Step 5: Remove L2VPN EVPN Instances")
            cleanup_lines.append("! ========================================")
            cleanup_lines.append("!")
            for instance in components['l2vpn_instances']:
                cleanup_lines.append(f"no l2vpn evpn instance {instance['id']} vlan-based")
            cleanup_lines.append("!")
            cleanup_lines.append("")
        
        # Step 6: Remove SVI interfaces
        if components['svi_interfaces']:
            cleanup_lines.append("! ========================================")
            cleanup_lines.append("! Step 6: Remove SVI Interfaces")
            cleanup_lines.append("! ========================================")
            cleanup_lines.append("!")
            for svi in components['svi_interfaces']:
                # Skip management VLAN 1 and special VLANs 50, 51, 52
                if svi['id'] not in ['1'] + list(self.excluded_vlans):
                    cleanup_lines.append(f"no interface Vlan{svi['id']}")
            cleanup_lines.append("!")
            cleanup_lines.append("")
        
        # Step 7: Remove VLAN VNI configurations (member vni with VNI numbers)
        vni_vlan_configs = [vc for vc in components['vlan_configs'] 
                           if vc.get('vni') and not vc.get('evpn_instance') 
                           and vc['id'] not in self.excluded_vlans]
        if vni_vlan_configs:
            cleanup_lines.append("! ========================================")
            cleanup_lines.append("! Step 7: Remove VLAN VNI Configurations")
            cleanup_lines.append("! ========================================")
            cleanup_lines.append("!")
            for vlan_cfg in vni_vlan_configs:
                cleanup_lines.append(f"vlan configuration {vlan_cfg['id']}")
                cleanup_lines.append(f" no member vni {vlan_cfg['vni']}")
                cleanup_lines.append(" exit")
            cleanup_lines.append("!")
            cleanup_lines.append("")
        
        # Step 8: Remove VLANs
        if components['vlans']:
            cleanup_lines.append("! ========================================")
            cleanup_lines.append("! Step 8: Remove EVPN VLANs")
            cleanup_lines.append("! ========================================")
            cleanup_lines.append("!")
            # Exclude VLAN 1 and special VLANs 50, 51, 52
            vlan_ids = [v['id'] for v in components['vlans'] 
                       if v['id'] not in ['1'] + list(self.excluded_vlans)]
            if vlan_ids:
                cleanup_lines.append(f"no vlan {','.join(vlan_ids)}")
            cleanup_lines.append("!")
            cleanup_lines.append("")
        
        # Step 9: Remove VRF definitions
        if components['vrfs']:
            cleanup_lines.append("! ========================================")
            cleanup_lines.append("! Step 9: Remove VRF Definitions")
            cleanup_lines.append("! ========================================")
            cleanup_lines.append("!")
            for vrf in components['vrfs']:
                cleanup_lines.append(f"no vrf definition {vrf['name']}")
            cleanup_lines.append("!")
            cleanup_lines.append("")
        
        # Step 10: Remove multicast routing for VRFs
        if components['vrfs']:
            cleanup_lines.append("! ========================================")
            cleanup_lines.append("! Step 10: Remove VRF Multicast Routing")
            cleanup_lines.append("! ========================================")
            cleanup_lines.append("!")
            for vrf in components['vrfs']:
                cleanup_lines.append(f"no ip multicast-routing vrf {vrf['name']}")
            cleanup_lines.append("!")
            cleanup_lines.append("")
        
        # Step 11: Remove BGP completely (optional)
        if components['bgp_evpn']:
            cleanup_lines.append("! ========================================")
            cleanup_lines.append("! Step 11: Remove BGP Completely (Optional)")
            cleanup_lines.append("! ========================================")
            cleanup_lines.append("!")
            cleanup_lines.append("no router bgp 65001")
            cleanup_lines.append("!")
            cleanup_lines.append("")
        
        # Step 12: Save configuration
        cleanup_lines.append("! ========================================")
        cleanup_lines.append("! Step 12: Save Configuration")
        cleanup_lines.append("! ========================================")
        cleanup_lines.append("!")
        cleanup_lines.append("end")
        cleanup_lines.append("write memory")
        cleanup_lines.append("!")
        
        return '\n'.join(cleanup_lines)
    
    def process_device(self, config_file: Path) -> Tuple[str, str]:
        """Process a single device configuration"""
        
        print(f"Processing {config_file.name}...")
        
        # Parse the running config
        components = self.parse_running_config(config_file)
        
        device_name = components['hostname'] or config_file.stem.replace('_running', '')
        
        # Generate cleanup config
        cleanup_config = self.generate_cleanup_config(components, device_name)
        
        # Write cleanup config to file
        output_file = self.output_dir / f"{device_name}_evpn_cleanup.cfg"
        with open(output_file, 'w') as f:
            f.write(cleanup_config)
        
        print(f"  ✓ Generated cleanup config: {output_file.name}")
        
        # Generate summary
        summary = {
            'device': device_name,
            'vrfs': len(components['vrfs']),
            'vlans': len(components['vlans']),
            'l2vpn_instances': len(components['l2vpn_instances']),
            'nve_interfaces': len(components['nve_interfaces']),
            'svi_interfaces': len(components['svi_interfaces']),
            'has_bgp_evpn': components['bgp_evpn']
        }
        
        return device_name, summary
    
    def generate_master_script(self, summaries: Dict):
        """Generate master cleanup script for all devices"""
        
        script_lines = []
        script_lines.append("#!/bin/bash")
        script_lines.append("#")
        script_lines.append("# BGP EVPN Cleanup Master Script")
        script_lines.append(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        script_lines.append("#")
        script_lines.append("# This script applies EVPN cleanup configurations to all devices")
        script_lines.append("#")
        script_lines.append("")
        script_lines.append("set -e")
        script_lines.append("")
        script_lines.append("# Color codes for output")
        script_lines.append('GREEN="\\033[0;32m"')
        script_lines.append('RED="\\033[0;31m"')
        script_lines.append('YELLOW="\\033[1;33m"')
        script_lines.append('NC="\\033[0m" # No Color')
        script_lines.append("")
        script_lines.append("SCRIPT_DIR=\"$( cd \"$( dirname \"${BASH_SOURCE[0]}\" )\" && pwd )\"")
        script_lines.append("CLEANUP_DIR=\"${SCRIPT_DIR}/evpn_cleanup_configs\"")
        script_lines.append("LOG_DIR=\"${SCRIPT_DIR}/cleanup_logs\"")
        script_lines.append("TIMESTAMP=$(date +%Y%m%d_%H%M%S)")
        script_lines.append("")
        script_lines.append("mkdir -p \"${LOG_DIR}\"")
        script_lines.append("")
        script_lines.append('echo -e "${YELLOW}========================================${NC}"')
        script_lines.append('echo -e "${YELLOW}BGP EVPN Cleanup Script${NC}"')
        script_lines.append('echo -e "${YELLOW}========================================${NC}"')
        script_lines.append('echo ""')
        script_lines.append("")
        script_lines.append("# Device list")
        script_lines.append("DEVICES=(")
        for device in sorted(summaries.keys()):
            script_lines.append(f'  "{device}"')
        script_lines.append(")")
        script_lines.append("")
        script_lines.append('echo -e "${YELLOW}Devices to clean:${NC}"')
        script_lines.append('for device in "${DEVICES[@]}"; do')
        script_lines.append('  echo "  - $device"')
        script_lines.append('done')
        script_lines.append('echo ""')
        script_lines.append("")
        script_lines.append('read -p "Do you want to proceed with cleanup? (yes/no): " CONFIRM')
        script_lines.append('if [ "$CONFIRM" != "yes" ]; then')
        script_lines.append('  echo -e "${RED}Cleanup cancelled.${NC}"')
        script_lines.append('  exit 1')
        script_lines.append('fi')
        script_lines.append('echo ""')
        script_lines.append("")
        script_lines.append("# Apply cleanup to each device")
        script_lines.append('for device in "${DEVICES[@]}"; do')
        script_lines.append('  echo -e "${YELLOW}Processing $device...${NC}"')
        script_lines.append('  ')
        script_lines.append('  CLEANUP_FILE="${CLEANUP_DIR}/${device}_evpn_cleanup.cfg"')
        script_lines.append('  LOG_FILE="${LOG_DIR}/${device}_cleanup_${TIMESTAMP}.log"')
        script_lines.append('  ')
        script_lines.append('  if [ ! -f "$CLEANUP_FILE" ]; then')
        script_lines.append('    echo -e "${RED}  ✗ Cleanup file not found: $CLEANUP_FILE${NC}"')
        script_lines.append('    continue')
        script_lines.append('  fi')
        script_lines.append('  ')
        script_lines.append('  # TODO: Add your device connection and config application logic here')
        script_lines.append('  # Example using expect or PyATS:')
        script_lines.append('  # pyats run job apply_config_job.py --testbed-file evpn_testbed.yaml \\')
        script_lines.append('  #   --device "$device" --config-file "$CLEANUP_FILE" --log-file "$LOG_FILE"')
        script_lines.append('  ')
        script_lines.append('  echo -e "${GREEN}  ✓ Cleanup config ready: $CLEANUP_FILE${NC}"')
        script_lines.append('  echo "    Review and apply manually or integrate with automation"')
        script_lines.append('done')
        script_lines.append("")
        script_lines.append('echo ""')
        script_lines.append('echo -e "${GREEN}========================================${NC}"')
        script_lines.append('echo -e "${GREEN}Cleanup configs generated successfully!${NC}"')
        script_lines.append('echo -e "${GREEN}========================================${NC}"')
        script_lines.append('echo ""')
        script_lines.append('echo "Next steps:"')
        script_lines.append('echo "1. Review cleanup configs in: ${CLEANUP_DIR}"')
        script_lines.append('echo "2. Apply configs manually or via automation"')
        script_lines.append('echo "3. Verify EVPN components are removed"')
        script_lines.append('echo "4. Check that ISIS/OSPF remain intact"')
        script_lines.append("")
        
        script_file = self.output_dir / "apply_evpn_cleanup.sh"
        with open(script_file, 'w') as f:
            f.write('\n'.join(script_lines))
        
        os.chmod(script_file, 0o755)
        print(f"\n✓ Generated master script: {script_file.name}")
    
    def generate_summary_report(self, summaries: Dict):
        """Generate summary report"""
        
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("BGP EVPN Cleanup Summary Report")
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("=" * 80)
        report_lines.append("")
        
        for device, summary in sorted(summaries.items()):
            report_lines.append(f"Device: {device}")
            report_lines.append(f"  VRFs to remove:          {summary['vrfs']}")
            report_lines.append(f"  VLANs to remove:         {summary['vlans']}")
            report_lines.append(f"  L2VPN instances:         {summary['l2vpn_instances']}")
            report_lines.append(f"  NVE interfaces:          {summary['nve_interfaces']}")
            report_lines.append(f"  SVI interfaces:          {summary['svi_interfaces']}")
            report_lines.append(f"  Has BGP EVPN:            {'Yes' if summary['has_bgp_evpn'] else 'No'}")
            report_lines.append("")
        
        report_lines.append("=" * 80)
        report_lines.append("Total Summary:")
        report_lines.append(f"  Devices processed:       {len(summaries)}")
        report_lines.append(f"  Total VRFs:              {sum(s['vrfs'] for s in summaries.values())}")
        report_lines.append(f"  Total VLANs:             {sum(s['vlans'] for s in summaries.values())}")
        report_lines.append(f"  Total L2VPN instances:   {sum(s['l2vpn_instances'] for s in summaries.values())}")
        report_lines.append("=" * 80)
        report_lines.append("")
        report_lines.append("Preserved Components:")
        report_lines.append("  ✓ ISIS routing protocol")
        report_lines.append("  ✓ OSPF routing protocol")
        report_lines.append("  ✓ Physical interfaces")
        report_lines.append("  ✓ Management VRF")
        report_lines.append("  ✓ AAA configuration")
        report_lines.append("  ✓ Basic device settings")
        report_lines.append("")
        
        report_file = self.output_dir / "cleanup_summary.txt"
        with open(report_file, 'w') as f:
            f.write('\n'.join(report_lines))
        
        print(f"✓ Generated summary report: {report_file.name}")
        
        # Also print to console
        print("\n" + '\n'.join(report_lines))
    
    def run(self):
        """Main execution"""
        
        print(f"\n{'=' * 80}")
        print("BGP EVPN Cleanup Configuration Generator")
        print(f"{'=' * 80}\n")
        
        # Find all running config files
        config_files = list(self.config_dir.glob("*_running.cfg"))
        
        if not config_files:
            print(f"ERROR: No running config files found in {self.config_dir}")
            sys.exit(1)
        
        print(f"Found {len(config_files)} device configurations\n")
        
        # Process each device
        summaries = {}
        for config_file in sorted(config_files):
            device_name, summary = self.process_device(config_file)
            summaries[device_name] = summary
        
        print(f"\n{'=' * 80}\n")
        
        # Generate master script
        self.generate_master_script(summaries)
        
        # Generate summary report
        self.generate_summary_report(summaries)
        
        print(f"\n{'=' * 80}")
        print("✓ All cleanup configurations generated successfully!")
        print(f"{'=' * 80}\n")
        print(f"Output directory: {self.output_dir}")
        print(f"\nNext steps:")
        print(f"  1. Review cleanup configs in: {self.output_dir}")
        print(f"  2. Review summary report: {self.output_dir}/cleanup_summary.txt")
        print(f"  3. Apply configs manually or run: {self.output_dir}/apply_evpn_cleanup.sh")
        print()


def main():
    """Main entry point"""
    #Get the running config DIR
    
    # Default paths
    script_dir = Path(__file__).parent
    default_config_dir = script_dir / "device_configs" / "20260205_155452" / "running_configs"
    default_output_dir = script_dir / "evpn_cleanup_configs"
    
    # Parse arguments
    if len(sys.argv) > 1:
        config_dir = sys.argv[1]
    else:
        config_dir = default_config_dir
    
    if len(sys.argv) > 2:
        output_dir = sys.argv[2]
    else:
        output_dir = default_output_dir
    
    # Validate config directory
    if not Path(config_dir).exists():
        print(f"ERROR: Config directory not found: {config_dir}")
        print(f"\nUsage: {sys.argv[0]} [config_dir] [output_dir]")
        sys.exit(1)
    
    # Create generator and run
    generator = EVPNCleanupGenerator(config_dir, output_dir)
    generator.run()


if __name__ == "__main__":
    main()
