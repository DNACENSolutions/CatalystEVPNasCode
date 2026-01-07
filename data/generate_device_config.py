#!/usr/bin/env python3
"""
BGP EVPN Device Configuration Generator

This script generates device-specific configurations using the YAML data model
and the BGP_EVPN_rev2 Jinja2 templates.

Usage:
    python generate_device_config.py --device leaf01.dcloud.cisco.com --template FABRIC-VRF
    python generate_device_config.py --device spine01.dcloud.cisco.com --template FABRIC-EVPN
    python generate_device_config.py --device border01.dcloud.cisco.com --all-templates
"""

import yaml
import argparse
import sys
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, Template
from yaml_to_template_vars import BGPEVPNDataModelConverter


class BGPEVPNConfigGenerator:
    """Generates device configurations from YAML data model and Jinja2 templates."""
    
    def __init__(self, data_model_path: str, templates_dir: str):
        """Initialize the configuration generator."""
        self.data_model_path = Path(data_model_path)
        self.templates_dir = Path(templates_dir)
        self.converter = BGPEVPNDataModelConverter(data_model_path)
        
        # Setup Jinja2 environment
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Available templates
        self.available_templates = {
            'DEFN-VRF': 'DEFN-VRF.j2',
            'DEFN-ROLES': 'DEFN-ROLES.j2',
            'DEFN-LOOPBACKS': 'DEFN-LOOPBACKS.j2',
            'DEFN-OVERLAY': 'DEFN-OVERLAY.j2',
            'DEFN-L3OUT': 'DEFN-L3OUT.j2',
            'DEFN-MCAST': 'DEFN-MCAST.j2',
            'DEFN-VNIOFFSETS': 'DEFN-VNIOFFSETS.j2',
            'DEFN-NAC-IOT': 'DEFN-NAC-IOT.j2',
            'DEFN-IPSEC': 'DEFN-IPSEC.j2',
            'FABRIC-VRF': 'FABRIC-VRF.j2',
            'FABRIC-LOOPBACKS': 'FABRIC-LOOPBACKS.j2',
            'FABRIC-NVE': 'FABRIC-NVE.j2',
            'FABRIC-MCAST': 'FABRIC-MCAST.j2',
            'FABRIC-EVPN': 'FABRIC-EVPN.j2',
            'FABRIC-OVERLAY': 'FABRIC-OVERLAY.j2',
            'FABRIC-NAC-IOT': 'FABRIC-NAC-IOT.j2',
            'FABRIC-IPSEC': 'FABRIC-IPSEC.j2'
        }
    
    def get_device_list(self) -> list:
        """Get list of all devices from the data model."""
        all_devices = set()
        for role_devices in self.converter.data_model['devices']['roles'].values():
            all_devices.update(role_devices)
        return sorted(list(all_devices))
    
    def get_device_role(self, device_hostname: str) -> str:
        """Get the primary role of a device."""
        roles = self.converter.data_model['devices']['roles']
        
        if device_hostname in roles.get('spine', []):
            return 'spine'
        elif device_hostname in roles.get('border', []):
            return 'border'
        elif device_hostname in roles.get('leaf', []):
            return 'leaf'
        else:
            return 'unknown'
    
    def generate_config(self, device_hostname: str, template_name: str) -> str:
        """Generate configuration for a specific device and template."""
        if template_name not in self.available_templates:
            raise ValueError(f"Template {template_name} not found. Available: {list(self.available_templates.keys())}")
        
        # Get template variables for the device
        template_vars = self.converter.generate_device_specific_vars(device_hostname)
        
        # Load and render the template
        template_file = self.available_templates[template_name]
        
        try:
            # For definition templates, we need to render them as-is
            if template_name.startswith('DEFN-'):
                template = self.jinja_env.get_template(template_file)
                config = template.render(**template_vars)
            else:
                # For fabric templates, we need to handle the macro-based structure
                config = self._render_fabric_template(template_file, template_vars, device_hostname)
            
            return config
            
        except Exception as e:
            raise RuntimeError(f"Error rendering template {template_name}: {str(e)}")
    
    def _render_fabric_template(self, template_file: str, template_vars: dict, device_hostname: str) -> str:
        """Render fabric templates that use macros."""
        try:
            # Read the template file
            template_path = self.templates_dir / template_file
            with open(template_path, 'r') as f:
                template_content = f.read()
            
            # Create a custom template that includes all definitions and calls the macro
            wrapper_template = f"""
{{% include "DEFN-VRF.j2" %}}
{{% include "DEFN-ROLES.j2" %}}
{{% include "DEFN-LOOPBACKS.j2" %}}
{{% include "DEFN-OVERLAY.j2" %}}
{{% include "DEFN-L3OUT.j2" %}}
{{% include "DEFN-MCAST.j2" %}}
{{% include "DEFN-VNIOFFSETS.j2" %}}
{{% include "DEFN-NAC-IOT.j2" %}}
{{% include "DEFN-IPSEC.j2" %}}
{{% include "FUNC-OBJECT-MACROS.j2" %}}

{template_content}

{{% if template_file == "FABRIC-VRF.j2" %}}
{{{{ vrfDefinitionBuild(DEFN_VRF, DEFN_VRF_TO_NODE, "{device_hostname}", DEFN_LOOP_UNDERLAY, FABRIC_BGP_ASN) }}}}
{{% elif template_file == "FABRIC-OVERLAY.j2" %}}
{{{{ overlayBuild(DEFN_VRF, DEFN_VRF_TO_NODE, "{device_hostname}", FABRIC_BGP_ASN, DEFN_OVERLAY, DEFN_NODE_ROLES, L2VNIOFFSET) }}}}
{{% endif %}}
"""
            
            template = Template(wrapper_template)
            return template.render(**template_vars)
            
        except Exception as e:
            # Fallback to simple template rendering
            template = self.jinja_env.get_template(template_file)
            return template.render(**template_vars)
    
    def generate_all_configs(self, device_hostname: str) -> dict:
        """Generate all applicable configurations for a device."""
        device_role = self.get_device_role(device_hostname)
        configs = {}
        
        # Generate definition templates (these are global)
        definition_templates = [t for t in self.available_templates.keys() if t.startswith('DEFN-')]
        
        # Generate fabric templates based on device role
        fabric_templates = []
        if device_role in ['spine', 'leaf', 'border']:
            fabric_templates = [
                'FABRIC-VRF',
                'FABRIC-LOOPBACKS',
                'FABRIC-NVE',
                'FABRIC-MCAST',
                'FABRIC-EVPN'
            ]
            
            # Add overlay only for leaf and border devices
            if device_role in ['leaf', 'border']:
                fabric_templates.append('FABRIC-OVERLAY')
            
            # Add NAC-IoT for leaf devices
            if device_role == 'leaf':
                fabric_templates.append('FABRIC-NAC-IOT')
            
            # Add IPSec for border devices
            if device_role == 'border':
                fabric_templates.append('FABRIC-IPSEC')
        
        # Generate configurations
        all_templates = definition_templates + fabric_templates
        
        for template_name in all_templates:
            try:
                config = self.generate_config(device_hostname, template_name)
                configs[template_name] = config
            except Exception as e:
                configs[template_name] = f"Error generating {template_name}: {str(e)}"
        
        return configs
    
    def save_device_configs(self, device_hostname: str, output_dir: str):
        """Save all device configurations to separate files."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        configs = self.generate_all_configs(device_hostname)
        
        for template_name, config in configs.items():
            filename = f"{device_hostname}_{template_name}.cfg"
            filepath = output_path / filename
            
            with open(filepath, 'w') as f:
                f.write(f"! Configuration generated from {template_name} template\n")
                f.write(f"! Device: {device_hostname}\n")
                f.write(f"! Generated by BGP EVPN Config Generator\n")
                f.write("!\n")
                f.write(config)
            
            print(f"Saved: {filepath}")


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(
        description="Generate BGP EVPN device configurations from YAML data model"
    )
    parser.add_argument(
        '--data-model', '-d',
        default='bgp_evpn_data_model.yml',
        help="YAML data model file (default: bgp_evpn_data_model.yml)"
    )
    parser.add_argument(
        '--templates-dir', '-t',
        default='BGP_EVPN_rev2',
        help="Templates directory (default: BGP_EVPN_rev2)"
    )
    parser.add_argument(
        '--device',
        required=True,
        help="Device hostname to generate config for"
    )
    parser.add_argument(
        '--template',
        help="Specific template to generate (e.g., FABRIC-VRF)"
    )
    parser.add_argument(
        '--all-templates',
        action='store_true',
        help="Generate all applicable templates for the device"
    )
    parser.add_argument(
        '--output-dir', '-o',
        help="Output directory for configuration files"
    )
    parser.add_argument(
        '--list-devices',
        action='store_true',
        help="List all available devices"
    )
    parser.add_argument(
        '--list-templates',
        action='store_true',
        help="List all available templates"
    )
    
    args = parser.parse_args()
    
    # Initialize generator
    try:
        generator = BGPEVPNConfigGenerator(args.data_model, args.templates_dir)
    except Exception as e:
        print(f"Error initializing generator: {e}")
        sys.exit(1)
    
    # List devices if requested
    if args.list_devices:
        devices = generator.get_device_list()
        print("Available devices:")
        for device in devices:
            role = generator.get_device_role(device)
            print(f"  {device} ({role})")
        return
    
    # List templates if requested
    if args.list_templates:
        print("Available templates:")
        for template in generator.available_templates.keys():
            print(f"  {template}")
        return
    
    # Validate device exists
    if args.device not in generator.get_device_list():
        print(f"Error: Device '{args.device}' not found in data model")
        print("Use --list-devices to see available devices")
        sys.exit(1)
    
    # Generate configurations
    try:
        if args.all_templates:
            if args.output_dir:
                generator.save_device_configs(args.device, args.output_dir)
            else:
                configs = generator.generate_all_configs(args.device)
                for template_name, config in configs.items():
                    print(f"\n{'='*60}")
                    print(f"Template: {template_name}")
                    print(f"Device: {args.device}")
                    print('='*60)
                    print(config)
        
        elif args.template:
            config = generator.generate_config(args.device, args.template)
            
            if args.output_dir:
                output_path = Path(args.output_dir)
                output_path.mkdir(parents=True, exist_ok=True)
                filename = f"{args.device}_{args.template}.cfg"
                filepath = output_path / filename
                
                with open(filepath, 'w') as f:
                    f.write(f"! Configuration generated from {args.template} template\n")
                    f.write(f"! Device: {args.device}\n")
                    f.write("!\n")
                    f.write(config)
                
                print(f"Configuration saved to: {filepath}")
            else:
                print(config)
        
        else:
            print("Error: Must specify either --template or --all-templates")
            sys.exit(1)
    
    except Exception as e:
        print(f"Error generating configuration: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
