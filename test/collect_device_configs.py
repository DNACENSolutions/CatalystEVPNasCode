#!/usr/bin/env python3
"""
PyATS Script to Collect Device Configurations from EVPN Testbed

This script connects to all network devices in the testbed and collects:
- Running configuration
- Startup configuration (if available)
- Device information (version, inventory)

Usage:
    python collect_device_configs.py --testbed evpn_testbed.yaml
    python collect_device_configs.py --testbed evpn_testbed.yaml --devices TB16-Fusion,TB16-SJ-BORDER-1
    python collect_device_configs.py --testbed evpn_testbed.yaml --output-dir ./configs
"""

import os
import sys
import logging
import argparse
from datetime import datetime
from pathlib import Path

# PyATS imports
from pyats import aetest
from pyats.topology import loader
from genie.testbed import load

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CommonSetup(aetest.CommonSetup):
    """Common Setup section to connect to all devices"""

    def clear_console(self, device):
        """Clear console and ensure device is in a clean state"""
        
        try:
            logger.info(f"Clearing console for {device.name}...")
            
            # Use a simpler approach - just send commands and wait
            import time

            # # Send multiple Ctrl+C to break out of any running commands or config mode
            # for _ in range(3):
            #     device.transmit('\x03')  # Ctrl+C
            #     time.sleep(0.5)
            
            # # Send multiple 'end' commands to exit config mode
            # for _ in range(3):
            #     device.transmit('end\r')
            #     time.sleep(0.5)
            
            # # Send 'exit' to exit any subshells
            # for _ in range(2):
            #     device.transmit('exit\r')
            #     time.sleep(0.5)
            
            # # Clear any pending input
            # device.transmit('\r')
            # time.sleep(0.5)
            
            # # For IOS/IOS-XE devices, ensure we're in exec mode
            # if device.os in ['iosxe', 'ios']:
            #     try:
            #         # Try to execute a simple command to verify we're in exec mode
            #         device.execute('show clock', timeout=5)
            #         logger.info(f"Console cleared successfully for {device.name}")
            #     except Exception as e:
            #         logger.warning(f"Console clearing verification failed for {device.name}: {str(e)}")
            #         # Try one more time with enable
            #         try:
            #             device.configure('')  # This will handle enable if needed
            #             device.execute('end')
            #             device.execute('show clock', timeout=5)
            #             logger.info(f"Console cleared after retry for {device.name}")
            #         except Exception as e2:
            #             logger.error(f"Failed to clear console for {device.name}: {str(e2)}")
            #             raise
            
        except Exception as e:
            logger.error(f"Error clearing console for {device.name}: {str(e)}")
            raise

    @aetest.subsection
    def connect_to_devices(self, testbed, device_list=None):
        """Connect to all devices in the testbed"""
        
        # Store testbed for later use
        self.parent.parameters['testbed'] = testbed
        
        # Define the list of core infrastructure devices to collect from
        core_devices = [
            'TB16-Fusion',
            'TB16-Spine',
            'TB16-SJ-BORDER-1',
            'TB16-SJ-BORDER-2',
            'TB16-SJ-Leaf-1',
            'TB16-SJ-Leaf-2',
            'TB16-SJ-Leaf-3',
            'TB16-SJ-Border-3'
            # 'TB16-eWLC-1',
            # 'TB16-eWLC-2',
            # 'TB16-NY-Border',
            # 'TB16-NY-Leaf'
        ]
        
        # Determine which devices to connect to
        if device_list:
            # User specified devices - use their list but exclude BASE-DEVICE
            devices_to_connect = [d for d in testbed.devices.values() 
                                if d.name in device_list and d.name != 'BASE-DEVICE']
        else:
            # Auto mode - only connect to core infrastructure devices
            devices_to_connect = [d for d in testbed.devices.values() 
                                if d.name in core_devices]
        
        logger.info(f"Attempting to connect to {len(devices_to_connect)} devices")
        
        connected_devices = []
        failed_devices = []
        
        for device in devices_to_connect:
            try:
                logger.info(f"Connecting to {device.name}...")
                device.connect(log_stdout=False, learn_hostname=True)
                
                # Clear console to ensure clean state
                try:
                    self.clear_console(device)
                except Exception as e:
                    logger.warning(f"Console clearing failed for {device.name}, but continuing: {str(e)}")
                
                connected_devices.append(device)
                logger.info(f"Successfully connected to {device.name}")
            except Exception as e:
                logger.error(f"Failed to connect to {device.name}: {str(e)}")
                failed_devices.append((device.name, str(e)))
        
        # Store results
        self.parent.parameters['connected_devices'] = connected_devices
        self.parent.parameters['failed_devices'] = failed_devices
        
        logger.info(f"Connected to {len(connected_devices)} devices")
        if failed_devices:
            logger.warning(f"Failed to connect to {len(failed_devices)} devices")


class CollectConfigurations(aetest.Testcase):
    """Collect configurations from all connected devices"""

    @aetest.setup
    def setup(self, output_dir='./device_configs'):
        """Setup output directory"""
        
        # Create output directory with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.output_dir = Path(output_dir) / timestamp
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Configurations will be saved to: {self.output_dir}")
        
        # Create subdirectories
        (self.output_dir / 'running_configs').mkdir(exist_ok=True)
        (self.output_dir / 'startup_configs').mkdir(exist_ok=True)
        (self.output_dir / 'device_info').mkdir(exist_ok=True)

    def ensure_exec_mode(self, device):
        """Ensure device is in exec mode before executing commands"""
        
        try:
            # Send Ctrl+C to break any running commands
            device.transmit('\x03')
            device.receive(timeout=0.5)
            
            # Send 'end' to exit config mode if in it
            device.transmit('end\r')
            device.receive(timeout=0.5)
            
            # Clear the line
            device.transmit('\r')
            device.receive(timeout=0.5)
            
        except Exception as e:
            logger.debug(f"Minor issue ensuring exec mode for {device.name}: {str(e)}")

    @aetest.test
    def collect_running_config(self, connected_devices):
        """Collect running configuration from all devices"""
        
        logger.info("=" * 80)
        logger.info("Collecting Running Configurations")
        logger.info("=" * 80)
        
        for device in connected_devices:
            try:
                logger.info(f"Collecting running config from {device.name}...")
                
                # Ensure device is in clean state before collecting
                self.ensure_exec_mode(device)
                
                # Execute show running-config
                if device.os in ['iosxe', 'ios']:
                    output = device.execute('show running-config', timeout=120)
                elif device.os == 'aireos':
                    output = device.execute('show run-config', timeout=120)
                elif device.type == 'ise':
                    # ISE uses different commands
                    output = device.execute('show running-config', timeout=120)
                else:
                    output = device.execute('show running-config', timeout=120)
                
                # Save to file
                config_file = self.output_dir / 'running_configs' / f"{device.name}_running.cfg"
                with open(config_file, 'w') as f:
                    f.write(output)
                
                logger.info(f"Saved running config for {device.name} ({len(output)} bytes)")
                
            except Exception as e:
                logger.error(f"Failed to collect running config from {device.name}: {str(e)}")

    @aetest.test
    def collect_startup_config(self, connected_devices):
        """Collect startup configuration from all devices"""
        
        logger.info("=" * 80)
        logger.info("Collecting Startup Configurations")
        logger.info("=" * 80)
        
        for device in connected_devices:
            try:
                logger.info(f"Collecting startup config from {device.name}...")
                
                # Ensure device is in clean state before collecting
                self.ensure_exec_mode(device)
                
                # Execute show startup-config (not all devices support this)
                if device.os in ['iosxe', 'ios']:
                    output = device.execute('show startup-config', timeout=120)
                    
                    # Save to file
                    config_file = self.output_dir / 'startup_configs' / f"{device.name}_startup.cfg"
                    with open(config_file, 'w') as f:
                        f.write(output)
                    
                    logger.info(f"Saved startup config for {device.name} ({len(output)} bytes)")
                else:
                    logger.info(f"Startup config not applicable for {device.name} (OS: {device.os})")
                
            except Exception as e:
                logger.warning(f"Could not collect startup config from {device.name}: {str(e)}")

    @aetest.test
    def collect_device_info(self, connected_devices):
        """Collect device information (version, inventory, etc.)"""
        
        logger.info("=" * 80)
        logger.info("Collecting Device Information")
        logger.info("=" * 80)
        
        for device in connected_devices:
            try:
                logger.info(f"Collecting device info from {device.name}...")
                
                # Ensure device is in clean state before collecting
                self.ensure_exec_mode(device)
                
                info_lines = []
                info_lines.append(f"Device: {device.name}")
                info_lines.append(f"Type: {device.type}")
                info_lines.append(f"OS: {device.os}")
                info_lines.append(f"Role: {device.role if hasattr(device, 'role') else 'N/A'}")
                info_lines.append("=" * 80)
                
                # Collect version information
                if device.os in ['iosxe', 'ios']:
                    try:
                        version_output = device.execute('show version', timeout=60)
                        info_lines.append("\n### SHOW VERSION ###\n")
                        info_lines.append(version_output)
                    except Exception as e:
                        logger.warning(f"Could not get version from {device.name}: {str(e)}")
                    
                    # Ensure clean state between commands
                    self.ensure_exec_mode(device)
                    
                    # Collect inventory
                    try:
                        inventory_output = device.execute('show inventory', timeout=60)
                        info_lines.append("\n### SHOW INVENTORY ###\n")
                        info_lines.append(inventory_output)
                    except Exception as e:
                        logger.warning(f"Could not get inventory from {device.name}: {str(e)}")
                    
                    # Ensure clean state between commands
                    self.ensure_exec_mode(device)
                    
                    # Collect interface summary
                    try:
                        interface_output = device.execute('show ip interface brief', timeout=60)
                        info_lines.append("\n### SHOW IP INTERFACE BRIEF ###\n")
                        info_lines.append(interface_output)
                    except Exception as e:
                        logger.warning(f"Could not get interfaces from {device.name}: {str(e)}")
                
                # Save to file
                info_file = self.output_dir / 'device_info' / f"{device.name}_info.txt"
                with open(info_file, 'w') as f:
                    f.write('\n'.join(info_lines))
                
                logger.info(f"Saved device info for {device.name}")
                
            except Exception as e:
                logger.error(f"Failed to collect device info from {device.name}: {str(e)}")

    @aetest.test
    def generate_summary(self, connected_devices, failed_devices):
        """Generate a summary report"""
        
        logger.info("=" * 80)
        logger.info("Generating Summary Report")
        logger.info("=" * 80)
        
        summary_lines = []
        summary_lines.append("=" * 80)
        summary_lines.append("DEVICE CONFIGURATION COLLECTION SUMMARY")
        summary_lines.append("=" * 80)
        summary_lines.append(f"Collection Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        summary_lines.append(f"Output Directory: {self.output_dir}")
        summary_lines.append("")
        
        summary_lines.append(f"Successfully Connected Devices: {len(connected_devices)}")
        for device in connected_devices:
            summary_lines.append(f"  - {device.name} ({device.type})")
        summary_lines.append("")
        
        if failed_devices:
            summary_lines.append(f"Failed to Connect: {len(failed_devices)}")
            for device_name, error in failed_devices:
                summary_lines.append(f"  - {device_name}: {error}")
            summary_lines.append("")
        
        summary_lines.append("=" * 80)
        summary_lines.append("FILES COLLECTED:")
        summary_lines.append("=" * 80)
        
        # Count files in each directory
        running_configs = list((self.output_dir / 'running_configs').glob('*.cfg'))
        startup_configs = list((self.output_dir / 'startup_configs').glob('*.cfg'))
        device_infos = list((self.output_dir / 'device_info').glob('*.txt'))
        
        summary_lines.append(f"Running Configurations: {len(running_configs)}")
        for cfg in running_configs:
            summary_lines.append(f"  - {cfg.name}")
        summary_lines.append("")
        
        summary_lines.append(f"Startup Configurations: {len(startup_configs)}")
        for cfg in startup_configs:
            summary_lines.append(f"  - {cfg.name}")
        summary_lines.append("")
        
        summary_lines.append(f"Device Information Files: {len(device_infos)}")
        for info in device_infos:
            summary_lines.append(f"  - {info.name}")
        summary_lines.append("")
        
        summary_lines.append("=" * 80)
        
        # Save summary
        summary_file = self.output_dir / 'SUMMARY.txt'
        with open(summary_file, 'w') as f:
            f.write('\n'.join(summary_lines))
        
        # Print summary
        print('\n'.join(summary_lines))
        
        logger.info(f"Summary saved to: {summary_file}")


class CommonCleanup(aetest.CommonCleanup):
    """Common Cleanup section to disconnect from all devices"""

    @aetest.subsection
    def disconnect_from_devices(self, connected_devices):
        """Disconnect from all devices"""
        
        logger.info("Disconnecting from all devices...")
        
        for device in connected_devices:
            try:
                device.disconnect()
                logger.info(f"Disconnected from {device.name}")
            except Exception as e:
                logger.warning(f"Error disconnecting from {device.name}: {str(e)}")


def main():
    """Main function to parse arguments and run the script"""
    
    parser = argparse.ArgumentParser(
        description='Collect configurations from EVPN testbed devices',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Collect from all devices
  python collect_device_configs.py --testbed evpn_testbed.yaml
  
  # Collect from specific devices
  python collect_device_configs.py --testbed evpn_testbed.yaml --devices TB16-Fusion,TB16-SJ-BORDER-1
  
  # Specify custom output directory
  python collect_device_configs.py --testbed evpn_testbed.yaml --output-dir /tmp/configs
        """
    )
    
    parser.add_argument(
        '--testbed',
        type=str,
        required=True,
        help='Path to testbed YAML file'
    )
    
    parser.add_argument(
        '--devices',
        type=str,
        help='Comma-separated list of device names to collect from (default: all network devices)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='./device_configs',
        help='Output directory for collected configurations (default: ./device_configs)'
    )
    
    args = parser.parse_args()
    
    # Load testbed
    try:
        logger.info(f"Loading testbed from: {args.testbed}")
        testbed = load(args.testbed)
        logger.info(f"Loaded testbed: {testbed.name}")
        logger.info(f"Total devices in testbed: {len(testbed.devices)}")
    except Exception as e:
        logger.error(f"Failed to load testbed: {str(e)}")
        sys.exit(1)
    
    # Parse device list if provided
    device_list = None
    if args.devices:
        device_list = [d.strip() for d in args.devices.split(',')]
        logger.info(f"Will collect from specific devices: {device_list}")
    
    # Run the test
    aetest.main(
        testbed=testbed,
        device_list=device_list,
        output_dir=args.output_dir
    )


if __name__ == '__main__':
    main()
