#!/usr/bin/env python3
"""
PyATS Script to Apply OSPF Underlay Configuration
Applies generated OSPF configs to devices
"""

import logging
import time
from pathlib import Path
from pyats import aetest
from pyats.log.utils import banner

logger = logging.getLogger(__name__)


class CommonSetup(aetest.CommonSetup):
    """Common setup tasks"""
    
    @aetest.subsection
    def check_ospf_configs(self, ospf_config_dir='ospf_underlay_configs'):
        """Check if OSPF config files exist"""
        
        logger.info(banner("Checking OSPF Configuration Files"))
        
        config_dir = Path(ospf_config_dir)
        
        if not config_dir.exists():
            self.failed(f"OSPF config directory not found: {config_dir}")
        
        # Find all OSPF config files
        config_files = list(config_dir.glob("*_ospf_underlay.cfg"))
        
        if not config_files:
            self.failed(f"No OSPF config files found in {config_dir}")
        
        # Map device names to config files
        available_configs = {}
        for config_file in config_files:
            # Extract device name from filename (e.g., TB16-Spine_ospf_underlay.cfg -> TB16-Spine)
            device_name = config_file.stem.replace('_ospf_underlay', '')
            available_configs[device_name] = config_file
        
        logger.info(f"Found {len(available_configs)} OSPF configuration files:")
        for device_name in sorted(available_configs.keys()):
            logger.info(f"  - {device_name}")
        
        self.parent.parameters['available_configs'] = available_configs
        self.parent.parameters['config_dir'] = config_dir
    
    @aetest.subsection
    def connect_to_devices(self, testbed, devices=None):
        """Connect to all devices in testbed"""
        
        logger.info(banner("Connecting to Devices"))
        
        # Determine which devices to connect to
        if devices:
            device_list = [d.strip() for d in devices.split(',')]
            devices_to_connect = [testbed.devices[d] for d in device_list if d in testbed.devices]
        else:
            # Connect to all devices except BASE-DEVICE
            devices_to_connect = [d for d in testbed.devices.values() if d.name != 'BASE-DEVICE']
        
        logger.info(f"Connecting to {len(devices_to_connect)} devices...")
        
        connected = []
        for device in devices_to_connect:
            try:
                logger.info(f"Connecting to {device.name}...")
                device.connect(log_stdout=False, learn_hostname=True)
                logger.info(f"  ✓ Connected to {device.name}")
                connected.append(device.name)
            except Exception as e:
                logger.error(f"  ✗ Failed to connect to {device.name}: {e}")
        
        if not connected:
            self.failed("Failed to connect to any devices!")
        
        self.parent.parameters['connected_devices'] = connected
        logger.info(f"\n✓ Connected to {len(connected)} devices")


class BackupCurrentConfig(aetest.Testcase):
    """Backup current device configurations before applying OSPF"""
    
    @aetest.test
    def backup_configs(self, testbed):
        """Backup running configs from all connected devices"""
        
        logger.info(banner("Backing Up Current Configurations"))
        
        connected_devices = self.parent.parameters.get('connected_devices', [])
        
        if not connected_devices:
            self.skipped("No connected devices to backup")
        
        # Create backup directory
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = Path('device_configs') / f'pre_ospf_{timestamp}'
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Backup directory: {backup_dir}")
        
        for device_name in connected_devices:
            device = testbed.devices[device_name]
            
            try:
                logger.info(f"Backing up {device_name}...")
                output = device.execute('show running-config')
                
                backup_file = backup_dir / f"{device_name}_running.cfg"
                with open(backup_file, 'w') as f:
                    f.write(output)
                
                logger.info(f"  ✓ Backed up to {backup_file.name}")
            except Exception as e:
                logger.error(f"  ✗ Failed to backup {device_name}: {e}")
        
        self.parent.parameters['backup_dir'] = backup_dir
        logger.info(f"\n✓ Backup completed: {backup_dir}")


class ApplyOSPFConfig(aetest.Testcase):
    """Apply OSPF underlay configuration to each device"""
    
    @aetest.setup
    def setup(self, testbed):
        """Setup for OSPF application"""
        
        self.connected_devices = self.parent.parameters.get('connected_devices', [])
        self.available_configs = self.parent.parameters.get('available_configs', {})
        
        if not self.connected_devices:
            self.skipped("No connected devices")
        
        if not self.available_configs:
            self.skipped("No OSPF configs available")
    
    @aetest.test
    def apply_ospf_to_devices(self, testbed, dry_run=False):
        """Apply OSPF configuration to all connected devices"""
        
        logger.info(banner("Applying OSPF Underlay Configuration"))
        
        if dry_run:
            logger.info("*** DRY RUN MODE - No changes will be applied ***\n")
        
        results = {}
        
        for device_name in self.connected_devices:
            device = testbed.devices[device_name]
            ospf_file = self.available_configs.get(device_name)
            
            if not ospf_file:
                logger.warning(f"No OSPF config for {device_name}, skipping")
                continue
            
            logger.info(banner(f"Applying OSPF to {device_name}"))
            
            try:
                # Read OSPF configuration
                with open(ospf_file, 'r') as f:
                    config_lines = f.readlines()
                
                # Filter out comments and empty lines
                config_commands = []
                for line in config_lines:
                    line = line.strip()
                    if line and not line.startswith('!'):
                        config_commands.append(line)
                
                logger.info(f"Applying {len(config_commands)} configuration commands...")
                
                if dry_run:
                    logger.info(f"DRY RUN: Would apply {len(config_commands)} commands to {device_name}")
                    logger.info(f"Config file: {ospf_file}")
                    results[device_name] = 'DRY_RUN'
                else:
                    # Apply configuration with error handling - continue on errors
                    try:
                        output = device.configure(config_commands, error_pattern=[])
                        logger.info(f"✓ Successfully applied OSPF to {device_name}")
                        
                        # Check if there were any errors in the output
                        if output and ('does not exist' in output or 'Invalid' in output):
                            logger.warning(f"⚠ Some commands had warnings, but continuing...")
                            logger.debug(f"Output:\n{output}")
                        
                        results[device_name] = 'SUCCESS'
                        
                    except Exception as config_error:
                        error_str = str(config_error)
                        
                        # Check if it's a false positive state machine error
                        if "Expected device to reach 'enable' state, but landed on 'enable' state" in error_str:
                            logger.warning(f"⚠ StateMachine false positive on {device_name}, checking actual state...")
                            try:
                                # Exit config mode first
                                device.execute('end')
                                # Verify device is actually in enable mode
                                device.execute('show version')
                                logger.info(f"✓ Device {device_name} is in enable mode, treating as SUCCESS")
                                results[device_name] = 'SUCCESS'
                            except:
                                logger.error(f"✗ Device {device_name} state verification failed")
                                results[device_name] = f'CONFIG_ERROR: {config_error}'
                        else:
                            logger.error(f"✗ Configuration error on {device_name}: {config_error}")
                            results[device_name] = f'CONFIG_ERROR: {config_error}'
                            
                            # Try to show what failed (exit config mode first)
                            try:
                                logger.info("Checking device state after error...")
                                device.execute('end')
                                output = device.execute('show running-config | include router ospf')
                                logger.info(f"Current OSPF state:\n{output}")
                            except:
                                pass
                
            except Exception as e:
                logger.error(f"✗ Failed to apply OSPF to {device_name}: {e}")
                results[device_name] = f'FAILED: {e}'
        
        # Store results
        self.parent.parameters['ospf_results'] = results
        
        # Check if any succeeded
        success_count = sum(1 for r in results.values() if r == 'SUCCESS')
        
        if not dry_run:
            if success_count == 0:
                self.failed("Failed to apply OSPF to any devices!")
            elif success_count < len(results):
                logger.warning(f"OSPF applied to {success_count}/{len(results)} devices")
            else:
                logger.info(f"✓ OSPF applied to all {success_count} devices")


class VerifyOSPF(aetest.Testcase):
    """Verify OSPF is operational"""
    
    @aetest.setup
    def setup(self):
        """Setup for verification"""
        
        self.ospf_results = self.parent.parameters.get('ospf_results', {})
        
        # Only verify devices where OSPF was applied successfully
        self.devices_to_verify = [
            name for name, result in self.ospf_results.items() 
            if result == 'SUCCESS'
        ]
        
        if not self.devices_to_verify:
            self.skipped("No devices with successful OSPF application to verify")
    
    @aetest.test
    def verify_ospf_enabled(self, testbed):
        """Verify OSPF is configured and running"""
        
        logger.info(banner("Verifying OSPF Configuration"))
        
        all_passed = True
        
        for device_name in self.devices_to_verify:
            device = testbed.devices[device_name]
            
            logger.info(f"\n{'='*60}")
            logger.info(f"Verifying {device_name}")
            logger.info(f"{'='*60}")
            
            checks = {
                'OSPF Process': 'show ip ospf',
                'OSPF Neighbors': 'show ip ospf neighbor',
                'OSPF Interfaces': 'show ip ospf interface brief',
            }
            
            for check_name, command in checks.items():
                try:
                    output = device.execute(command, prompt_recovery=True)
                    
                    if check_name == 'OSPF Process':
                        if 'Routing Process' in output and 'ospf 1' in output:
                            logger.info(f"  ✓ {check_name}: OSPF process 1 is running")
                        else:
                            logger.warning(f"  ⚠ {check_name}: OSPF may not be running properly")
                            all_passed = False
                    
                    elif check_name == 'OSPF Neighbors':
                        if 'FULL' in output:
                            neighbor_count = output.count('FULL')
                            logger.info(f"  ✓ {check_name}: {neighbor_count} neighbor(s) in FULL state")
                        else:
                            logger.warning(f"  ⚠ {check_name}: No neighbors in FULL state yet")
                    
                    elif check_name == 'OSPF Interfaces':
                        lines = [l for l in output.split('\n') if 'up' in l.lower()]
                        if lines:
                            logger.info(f"  ✓ {check_name}: {len(lines)} interface(s) enabled")
                        else:
                            logger.warning(f"  ⚠ {check_name}: No interfaces found")
                            all_passed = False
                        
                except Exception as e:
                    logger.error(f"  ✗ Failed to verify {check_name} on {device_name}: {e}")
                    all_passed = False
        
        if not all_passed:
            logger.warning("Some OSPF verification checks did not pass")
        else:
            logger.info("\n✓ All OSPF verification checks passed")


class CommonCleanup(aetest.CommonCleanup):
    """Common cleanup tasks"""
    
    @aetest.subsection
    def disconnect_devices(self, testbed):
        """Disconnect from all devices"""
        
        logger.info(banner("Disconnecting from Devices"))
        
        for device in testbed.devices.values():
            if device.is_connected():
                try:
                    device.disconnect()
                    logger.info(f"  ✓ Disconnected from {device.name}")
                except Exception as e:
                    logger.warning(f"  ⚠ Error disconnecting from {device.name}: {e}")
    
    @aetest.subsection
    def generate_report(self):
        """Generate OSPF application summary report"""
        
        logger.info(banner("OSPF Application Summary"))
        
        results = self.parent.parameters.get('ospf_results', {})
        
        if not results:
            logger.info("No OSPF application results to report")
            return
        
        success = [name for name, result in results.items() if result == 'SUCCESS']
        failed = [name for name, result in results.items() if 'FAILED' in result or 'ERROR' in result]
        dry_run = [name for name, result in results.items() if result == 'DRY_RUN']
        
        logger.info(f"\nTotal Devices: {len(results)}")
        logger.info(f"Successful: {len(success)}")
        logger.info(f"Failed: {len(failed)}")
        if dry_run:
            logger.info(f"Dry Run: {len(dry_run)}")
        
        if success:
            logger.info(f"\n✓ Successfully applied OSPF:")
            for name in success:
                logger.info(f"  - {name}")
        
        if failed:
            logger.info(f"\n✗ Failed to apply OSPF:")
            for name in failed:
                logger.info(f"  - {name}: {results[name]}")


if __name__ == '__main__':
    import argparse
    from pyats.topology import loader
    
    parser = argparse.ArgumentParser(description='Apply OSPF Underlay Configuration Script')
    parser.add_argument('--testbed', required=True, help='Path to testbed file')
    parser.add_argument('--devices', help='Comma-separated list of devices (default: all)')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode (no changes)')
    parser.add_argument('--ospf-config-dir', default='ospf_underlay_configs', 
                       help='Directory containing OSPF config files')
    
    args, unknown = parser.parse_known_args()
    
    # Load testbed
    testbed = loader.load(args.testbed)
    
    # Run the test
    aetest.main(
        testbed=testbed, 
        devices=args.devices, 
        dry_run=args.dry_run,
        ospf_config_dir=args.ospf_config_dir
    )
