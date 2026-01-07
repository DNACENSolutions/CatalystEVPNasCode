#!/usr/bin/env python3
"""
BGP EVPN YAML Data Model to Template Variables Converter

This script converts the YAML data model (bgp_evpn_data_model.yml) into
the template variable format expected by the BGP_EVPN_rev2 Jinja2 templates.

Usage:
    python yaml_to_template_vars.py --input bgp_evpn_data_model.yml --output template_vars.yml
    python yaml_to_template_vars.py --input bgp_evpn_data_model.yml --device leaf01.dcloud.cisco.com
"""

import yaml
import argparse
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional


class BGPEVPNDataModelConverter:
    """Converts YAML data model to template variables format."""
    
    def __init__(self, data_model_path: str):
        """Initialize converter with data model file."""
        self.data_model_path = Path(data_model_path)
        self.data_model = self._load_data_model()
        
    def _load_data_model(self) -> Dict[str, Any]:
        """Load the YAML data model."""
        try:
            with open(self.data_model_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"Error: Data model file not found: {self.data_model_path}")
            sys.exit(1)
        except yaml.YAMLError as e:
            print(f"Error parsing YAML file: {e}")
            sys.exit(1)
    
    def convert_to_template_vars(self, device_hostname: Optional[str] = None) -> Dict[str, Any]:
        """Convert data model to template variables format."""
        template_vars = {}
        
        # Global fabric settings
        template_vars['FABRIC_BGP_ASN'] = self.data_model['fabric']['bgp_asn']
        template_vars['FABRIC_UNDERLAY'] = self.data_model['fabric']['underlay']
        template_vars['FABRIC_IPSEC_UNDERLAY'] = self.data_model['fabric']['ipsec_underlay']
        
        # VNI offsets
        template_vars['L2VNIOFFSET'] = self.data_model['vni_offsets']['l2_vni_offset']
        template_vars['L3VNIOFFSET'] = self.data_model['vni_offsets']['l3_vni_offset']
        
        # Multicast settings
        template_vars['FABRIC_RP_ADDR'] = self.data_model['multicast']['fabric_rp']['address']
        template_vars['FABRIC_RP_SCOPES'] = self.data_model['multicast']['fabric_rp']['scopes']
        template_vars['ENTERPRISE_RP_ADDR'] = self.data_model['multicast']['enterprise_rp']['address']
        template_vars['ENTERPRISE_RP_SCOPES'] = self.data_model['multicast']['enterprise_rp']['scopes']
        
        # Device roles - convert to template format
        template_vars['DEFN_NODE_ROLES'] = {
            'SPINE': self.data_model['devices']['roles']['spine'],
            'RR': self.data_model['devices']['roles']['route_reflector'],
            'CLIENT': self.data_model['devices']['roles']['client'],
            'BORDER': self.data_model['devices']['roles']['border']
        }
        
        # Loopback definitions
        template_vars['DEFN_LOOP_UNDERLAY'] = self.data_model['devices']['loopbacks']['underlay']
        template_vars['DEFN_LOOP_IPSEC'] = self.data_model['devices']['loopbacks']['ipsec']
        template_vars['DEFN_LOOP_MCLUSTER'] = self.data_model['devices']['loopbacks']['multi_cluster']
        template_vars['DEFN_LOOP_OVERLAY'] = self.data_model['devices']['loopbacks']['overlay_prefixes']
        template_vars['DEFN_LOOP_NAME'] = self.data_model['devices']['loopbacks']['interface_names']
        
        # VRF definitions
        template_vars['DEFN_VRF'] = self.data_model['vrfs']['definitions']
        template_vars['DEFN_VRF_TO_NODE'] = self.data_model['vrfs']['device_mappings']
        
        # Overlay networks - convert format
        template_vars['DEFN_OVERLAY'] = []
        for overlay in self.data_model['overlay_networks']:
            overlay_def = {
                'vrf': overlay['vrf'],
                'vlans': {}
            }
            for vlan_id, vlan_config in overlay['vlans'].items():
                overlay_def['vlans'][vlan_id] = {
                    'name': vlan_config['name'],
                    'ipaddr': vlan_config['ip_address'],
                    'mac': vlan_config['mac_address'],
                    'dhcp_helper': vlan_config['dhcp_helper'],
                    'bum_addr': vlan_config['bum_address']
                }
            template_vars['DEFN_OVERLAY'].append(overlay_def)
        
        # L3 external connectivity
        template_vars['DEFN_L3OUT'] = []
        for connection in self.data_model['l3_external']['connections']:
            l3out_def = {
                'vrf': connection['vrf'],
                'node': connection['device'],
                'neighbour_asn': connection['neighbor_asn'],
                'interfaces': {}
            }
            for intf_name, intf_config in connection['interfaces'].items():
                l3out_def['interfaces'][intf_name] = {
                    'name': intf_config['name'],
                    'vlan': intf_config['vlan'],
                    'ipaddr': intf_config['ip_address'],
                    'neighbour': intf_config['neighbor_ip']
                }
            template_vars['DEFN_L3OUT'].append(l3out_def)
        
        template_vars['DEFN_L3OUT_AGGREGATES'] = self.data_model['l3_external']['aggregate_routes']
        
        # NAC IoT
        template_vars['DEFN_NAC_IOT'] = []
        for server in self.data_model['network_access_control']['servers']:
            template_vars['DEFN_NAC_IOT'].append({
                'vrf': server['vrf'],
                'nac_ip': server['server_ip'],
                'nac_key': server['shared_key']
            })
        
        # IPSec tunnels
        template_vars['DEFN_IPSEC'] = {}
        for device, tunnels in self.data_model['ipsec']['tunnels'].items():
            template_vars['DEFN_IPSEC'][device] = []
            for tunnel in tunnels:
                template_vars['DEFN_IPSEC'][device].append({
                    'tun_ip': tunnel['tunnel_ip'],
                    'peer_ip': tunnel['peer_ip'],
                    'tun_dst': tunnel['tunnel_destination'],
                    'tun_mode': tunnel['tunnel_mode'],
                    'peer_bgp_asn': tunnel['peer_bgp_asn']
                })
        
        # Add device-specific context if provided
        if device_hostname:
            template_vars['__device'] = {'hostname': device_hostname}
            
            # Add device-specific VRF list
            if device_hostname in template_vars['DEFN_VRF_TO_NODE']:
                template_vars['vrf_list'] = []
                device_vrf_ids = template_vars['DEFN_VRF_TO_NODE'][device_hostname]
                for vrf_def in template_vars['DEFN_VRF']:
                    if vrf_def['id'] in device_vrf_ids:
                        template_vars['vrf_list'].append(vrf_def['name'])
        
        return template_vars
    
    def generate_device_specific_vars(self, device_hostname: str) -> Dict[str, Any]:
        """Generate device-specific template variables."""
        return self.convert_to_template_vars(device_hostname)
    
    def validate_data_model(self) -> List[str]:
        """Validate the data model for consistency."""
        errors = []
        
        # Check required fields
        required_fields = self.data_model.get('validation', {}).get('required_fields', [])
        for field_path in required_fields:
            if not self._check_field_exists(field_path):
                errors.append(f"Required field missing: {field_path}")
        
        # Check VRF ID uniqueness
        vrf_ids = [vrf['id'] for vrf in self.data_model['vrfs']['definitions']]
        if len(vrf_ids) != len(set(vrf_ids)):
            errors.append("VRF IDs must be unique")
        
        # Check that all devices in roles have underlay loopbacks
        all_devices = set()
        for role_devices in self.data_model['devices']['roles'].values():
            all_devices.update(role_devices)
        
        underlay_devices = set(self.data_model['devices']['loopbacks']['underlay'].keys())
        missing_loopbacks = all_devices - underlay_devices
        if missing_loopbacks:
            errors.append(f"Devices missing underlay loopbacks: {missing_loopbacks}")
        
        # Check VRF mappings reference valid VRF IDs
        valid_vrf_ids = set(vrf_ids)
        for device, mapped_vrfs in self.data_model['vrfs']['device_mappings'].items():
            invalid_vrfs = set(mapped_vrfs) - valid_vrf_ids
            if invalid_vrfs:
                errors.append(f"Device {device} references invalid VRF IDs: {invalid_vrfs}")
        
        return errors
    
    def _check_field_exists(self, field_path: str) -> bool:
        """Check if a nested field exists in the data model."""
        parts = field_path.split('.')
        current = self.data_model
        
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return False
        return True
    
    def save_template_vars(self, output_path: str, device_hostname: Optional[str] = None):
        """Save template variables to YAML file."""
        template_vars = self.convert_to_template_vars(device_hostname)
        
        with open(output_path, 'w') as f:
            yaml.dump(template_vars, f, default_flow_style=False, indent=2)
        
        print(f"Template variables saved to: {output_path}")


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(
        description="Convert BGP EVPN YAML data model to template variables"
    )
    parser.add_argument(
        '--input', '-i',
        required=True,
        help="Input YAML data model file"
    )
    parser.add_argument(
        '--output', '-o',
        help="Output template variables file"
    )
    parser.add_argument(
        '--device', '-d',
        help="Generate device-specific variables for this hostname"
    )
    parser.add_argument(
        '--validate', '-v',
        action='store_true',
        help="Validate the data model"
    )
    parser.add_argument(
        '--list-devices',
        action='store_true',
        help="List all devices in the data model"
    )
    
    args = parser.parse_args()
    
    # Initialize converter
    converter = BGPEVPNDataModelConverter(args.input)
    
    # Validate if requested
    if args.validate:
        errors = converter.validate_data_model()
        if errors:
            print("Validation errors found:")
            for error in errors:
                print(f"  - {error}")
            sys.exit(1)
        else:
            print("Data model validation passed!")
    
    # List devices if requested
    if args.list_devices:
        print("Devices in data model:")
        all_devices = set()
        for role, devices in converter.data_model['devices']['roles'].items():
            print(f"  {role.upper()}:")
            for device in devices:
                print(f"    - {device}")
                all_devices.add(device)
        print(f"\nTotal devices: {len(all_devices)}")
        return
    
    # Generate template variables
    if args.output:
        converter.save_template_vars(args.output, args.device)
    else:
        # Print to stdout
        template_vars = converter.convert_to_template_vars(args.device)
        print(yaml.dump(template_vars, default_flow_style=False, indent=2))


if __name__ == '__main__':
    main()
