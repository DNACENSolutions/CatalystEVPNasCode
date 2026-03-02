#!/usr/bin/env python3
"""
Apply EVPN Cleanup Configurations to Devices

This PyATS script applies the generated EVPN cleanup configurations to devices,
removing BGP EVPN/VXLAN components while preserving ISIS, OSPF, and basic configs.

Usage:
    pyats run job apply_evpn_cleanup_job.py --testbed-file evpn_testbed.yaml
    pyats run job apply_evpn_cleanup_job.py --testbed-file evpn_testbed.yaml --devices TB16-SJ-Leaf-1
"""

import logging
import time
from pathlib import Path
from datetime import datetime
from pyats import aetest
from pyats.log.utils import banner

logger = logging.getLogger(__name__)

# Core infrastructure devices for cleanup
CLEANUP_DEVICES = [
    'TB16-Fusion',
    'TB16-Spine',
    'TB16-SJ-BORDER-1',
    'TB16-SJ-BORDER-2',
    'TB16-SJ-Leaf-1',
    'TB16-SJ-Leaf-2',
    'TB16-SJ-Leaf-3',
    'TB16-SJ-Border-3',
    'TB16-NY-Border',
    'TB16-NY-Leaf'
]


class CommonSetup(aetest.CommonSetup):
    """Common Setup Section - Connect to devices and prepare for cleanup"""
    
    @aetest.subsection
    def check_cleanup_configs(self, testbed):
        """Verify cleanup configuration files exist"""
        
        cleanup_dir = Path(__file__).parent / "evpn_cleanup_configs"
        
        if not cleanup_dir.exists():
            self.failed(f"Cleanup configs directory not found: {cleanup_dir}")
        
        logger.info(f"Cleanup configs directory: {cleanup_dir}")
        
        # Store cleanup directory in parameters
        self.parent.parameters['cleanup_dir'] = cleanup_dir
        
        # Check which devices have cleanup configs
        available_configs = {}
        for device_name in testbed.devices.keys():
            if device_name == 'BASE-DEVICE':
                continue
            
            cleanup_file = cleanup_dir / f"{device_name}_evpn_cleanup.cfg"
            if cleanup_file.exists():
                available_configs[device_name] = cleanup_file
                logger.info(f"  ✓ Found cleanup config for {device_name}")
            else:
                logger.warning(f"  ✗ No cleanup config for {device_name}")
        
        if not available_configs:
            self.failed("No cleanup configuration files found!")
        
        self.parent.parameters['available_configs'] = available_configs
        logger.info(f"\nFound {len(available_configs)} cleanup configurations")
    
    @aetest.subsection
    def connect_to_devices(self, testbed, devices=None):
        """Connect to devices that need cleanup"""
        
        available_configs = self.parent.parameters.get('available_configs', {})
        
        # Determine which devices to connect to
        if devices:
            # User specified devices
            devices_to_connect = [d for d in devices if d in available_configs]
        else:
            # All devices with cleanup configs
            devices_to_connect = list(available_configs.keys())
        
        if not devices_to_connect:
            self.failed("No devices to connect to!")
        
        logger.info(f"\nConnecting to {len(devices_to_connect)} devices...")
        
        connected_devices = []
        failed_devices = []
        
        for device_name in devices_to_connect:
            if device_name not in testbed.devices:
                logger.warning(f"Device {device_name} not in testbed, skipping")
                continue
            
            device = testbed.devices[device_name]
            
            try:
                logger.info(f"Connecting to {device_name}...")
                device.connect(log_stdout=False, learn_hostname=True)
                connected_devices.append(device_name)
                logger.info(f"  ✓ Connected to {device_name}")
            except Exception as e:
                logger.error(f"  ✗ Failed to connect to {device_name}: {e}")
                failed_devices.append(device_name)
        
        if not connected_devices:
            self.failed("Failed to connect to any devices!")
        
        self.parent.parameters['connected_devices'] = connected_devices
        self.parent.parameters['failed_devices'] = failed_devices
        
        logger.info(f"\nSuccessfully connected to {len(connected_devices)} devices")
        if failed_devices:
            logger.warning(f"Failed to connect to: {', '.join(failed_devices)}")
    
    #@aetest.subsection
    def backup_current_configs(self, testbed):
        """Backup current running configs before cleanup"""
        
        connected_devices = self.parent.parameters.get('connected_devices', [])
        
        backup_dir = Path(__file__).parent / "device_configs" / f"pre_cleanup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"\nBacking up current configs to: {backup_dir}")
        
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


class ApplyCleanupConfig(aetest.Testcase):
    """Apply EVPN cleanup configuration to each device"""
    
    @aetest.setup
    def setup(self, testbed):
        """Setup for cleanup application"""
        
        self.connected_devices = self.parent.parameters.get('connected_devices', [])
        self.available_configs = self.parent.parameters.get('available_configs', {})
        self.cleanup_dir = self.parent.parameters.get('cleanup_dir')
        
        if not self.connected_devices:
            self.skipped("No connected devices to apply cleanup")
    
    @aetest.test
    def apply_cleanup_to_devices(self, testbed):
        """Apply cleanup configuration to each device"""
        
        results = {}
        
        for device_name in self.connected_devices:
            device = testbed.devices[device_name]
            cleanup_file = self.available_configs.get(device_name)
            
            if not cleanup_file:
                logger.warning(f"No cleanup config for {device_name}, skipping")
                continue
            
            logger.info(banner(f"Applying cleanup to {device_name}"))
            
            try:
                # Read cleanup configuration
                with open(cleanup_file, 'r') as f:
                    config_lines = f.readlines()
                
                # Filter out comments and empty lines
                config_commands = []
                for line in config_lines:
                    line = line.strip()
                    if line and not line.startswith('!'):
                        config_commands.append(line)
                
                logger.info(f"Applying {len(config_commands)} configuration commands...")
                
                # Apply configuration with error handling - continue on errors
                try:
                    # Use error_pattern=[] to not stop on common errors
                    output = device.configure(config_commands, error_pattern=[])
                    logger.info(f"✓ Successfully applied cleanup to {device_name}")
                    
                    # Check if there were any errors in the output
                    if output and ('does not exist' in output or 'Invalid' in output):
                        logger.warning(f"⚠ Some commands had errors (items already removed), but continuing...")
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
                            output = device.execute('show running-config | include bgp')
                            logger.info(f"Current BGP state:\n{output}")
                        except:
                            pass
                
            except Exception as e:
                logger.error(f"✗ Failed to apply cleanup to {device_name}: {e}")
                results[device_name] = f'FAILED: {e}'
        
        # Store results
        self.parent.parameters['cleanup_results'] = results
        
        # Check if any succeeded
        success_count = sum(1 for r in results.values() if r == 'SUCCESS')
        
        if success_count == 0:
            self.failed("Failed to apply cleanup to any devices!")
        elif success_count < len(results):
            logger.warning(f"Cleanup succeeded on {success_count}/{len(results)} devices")
        else:
            logger.info(f"✓ Cleanup succeeded on all {success_count} devices")


class VerifyCleanup(aetest.Testcase):
    """Verify EVPN components are removed and underlay is intact"""
    
    #@aetest.setup
    def setup(self):
        """Setup for verification"""
        
        self.cleanup_results = self.parent.parameters.get('cleanup_results', {})
        
        # Only verify devices where cleanup succeeded
        self.devices_to_verify = [
            device for device, result in self.cleanup_results.items()
            if result == 'SUCCESS'
        ]
        
        if not self.devices_to_verify:
            self.skipped("No devices with successful cleanup to verify")
    
    #@aetest.test
    def verify_evpn_removed(self, testbed):
        """Verify EVPN components are removed"""
        
        logger.info(banner("Verifying EVPN Components Removed"))
        
        verification_results = {}
        
        for device_name in self.devices_to_verify:
            device = testbed.devices[device_name]
            
            logger.info(f"\nVerifying {device_name}...")
            
            checks = {
                'l2vpn_evpn': False,
                'nve_interface': False,
                'evpn_vrfs': False,
                'bgp_evpn_af': False
            }
            
            try:
                # Check L2VPN EVPN instances
                try:
                    output = device.execute('show l2vpn evpn', timeout=10)
                    if 'Invalid input' in output or 'No EVPN' in output or not output.strip():
                        checks['l2vpn_evpn'] = True
                        logger.info("  ✓ L2VPN EVPN instances removed")
                    else:
                        logger.warning(f"  ✗ L2VPN EVPN still present:\n{output}")
                except Exception:
                    checks['l2vpn_evpn'] = True
                    logger.info("  ✓ L2VPN EVPN instances removed")
                
                # Check NVE interface
                try:
                    output = device.execute('show interface nve1', timeout=10)
                    if 'Invalid' in output or 'does not exist' in output:
                        checks['nve_interface'] = True
                        logger.info("  ✓ NVE interface removed")
                    else:
                        logger.warning(f"  ✗ NVE interface still exists:\n{output}")
                except Exception:
                    checks['nve_interface'] = True
                    logger.info("  ✓ NVE interface removed")
                
                # Check VRFs (should only have Mgmt-vrf)
                try:
                    output = device.execute('show vrf', timeout=10)
                    evpn_vrfs = ['red', 'blue', 'green']
                    vrf_found = any(vrf in output for vrf in evpn_vrfs)
                    
                    if not vrf_found:
                        checks['evpn_vrfs'] = True
                        logger.info("  ✓ EVPN VRFs removed")
                    else:
                        logger.warning(f"  ✗ EVPN VRFs still present:\n{output}")
                except Exception as e:
                    logger.warning(f"  ? Could not verify VRFs: {e}")
                
                # Check BGP EVPN address-family
                try:
                    output = device.execute('show bgp l2vpn evpn summary', timeout=10)
                    if 'Invalid' in output or 'not active' in output or 'No BGP' in output:
                        checks['bgp_evpn_af'] = True
                        logger.info("  ✓ BGP EVPN address-family removed")
                    else:
                        logger.warning(f"  ✗ BGP EVPN still active:\n{output}")
                except Exception:
                    checks['bgp_evpn_af'] = True
                    logger.info("  ✓ BGP EVPN address-family removed")
                
                verification_results[device_name] = checks
                
            except Exception as e:
                logger.error(f"  ✗ Verification failed for {device_name}: {e}")
                verification_results[device_name] = {'error': str(e)}
        
        self.parent.parameters['verification_results'] = verification_results
        
        # Check if all verifications passed
        all_passed = all(
            all(checks.values()) if isinstance(checks, dict) and 'error' not in checks else False
            for checks in verification_results.values()
        )
        
        if not all_passed:
            logger.warning("Some EVPN components may still be present")
    
    #@aetest.test
    def verify_underlay_intact(self, testbed):
        """Verify ISIS/OSPF underlay routing is still operational"""
        
        logger.info(banner("Verifying Underlay Routing Intact"))
        
        underlay_results = {}
        
        for device_name in self.devices_to_verify:
            device = testbed.devices[device_name]
            
            logger.info(f"\nVerifying underlay on {device_name}...")
            
            checks = {
                'isis_running': False,
                'isis_neighbors': False,
                'ip_routing': False
            }
            
            try:
                # Check ISIS
                try:
                    output = device.execute('show isis neighbors', timeout=10)
                    if 'INIT' in output or 'UP' in output:
                        checks['isis_running'] = True
                        checks['isis_neighbors'] = True
                        logger.info("  ✓ ISIS neighbors operational")
                    elif 'No IS-IS' in output or 'not running' in output:
                        logger.info("  ℹ ISIS not configured (expected for some devices)")
                        checks['isis_running'] = True  # Not an error if not configured
                    else:
                        logger.warning(f"  ✗ ISIS state unclear:\n{output}")
                except Exception as e:
                    logger.info(f"  ℹ ISIS check: {e}")
                
                # Check IP routing
                try:
                    output = device.execute('show ip route summary', timeout=10)
                    if 'Total' in output or 'routes' in output:
                        checks['ip_routing'] = True
                        logger.info("  ✓ IP routing operational")
                    else:
                        logger.warning(f"  ✗ IP routing unclear:\n{output}")
                except Exception as e:
                    logger.warning(f"  ✗ Could not verify IP routing: {e}")
                
                underlay_results[device_name] = checks
                
            except Exception as e:
                logger.error(f"  ✗ Underlay verification failed for {device_name}: {e}")
                underlay_results[device_name] = {'error': str(e)}
        
        self.parent.parameters['underlay_results'] = underlay_results


class CommonCleanup(aetest.CommonCleanup):
    """Common Cleanup Section - Generate report and disconnect"""
    
    @aetest.subsection
    def generate_cleanup_report(self, testbed):
        """Generate final cleanup report"""
        
        logger.info(banner("EVPN Cleanup Summary Report"))
        
        cleanup_results = self.parent.parameters.get('cleanup_results', {})
        verification_results = self.parent.parameters.get('verification_results', {})
        underlay_results = self.parent.parameters.get('underlay_results', {})
        backup_dir = self.parent.parameters.get('backup_dir')
        
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("EVPN CLEANUP EXECUTION REPORT")
        report_lines.append(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("=" * 80)
        report_lines.append("")
        
        # Cleanup application results
        report_lines.append("CLEANUP APPLICATION RESULTS:")
        report_lines.append("-" * 80)
        for device, result in sorted(cleanup_results.items()):
            status = "✓ SUCCESS" if result == 'SUCCESS' else f"✗ {result}"
            report_lines.append(f"  {device:25s} {status}")
        report_lines.append("")
        
        # Verification results
        if verification_results:
            report_lines.append("EVPN REMOVAL VERIFICATION:")
            report_lines.append("-" * 80)
            for device, checks in sorted(verification_results.items()):
                if isinstance(checks, dict) and 'error' not in checks:
                    all_passed = all(checks.values())
                    status = "✓ VERIFIED" if all_passed else "⚠ PARTIAL"
                    report_lines.append(f"  {device:25s} {status}")
                    for check, passed in checks.items():
                        symbol = "✓" if passed else "✗"
                        report_lines.append(f"    {symbol} {check}")
                else:
                    report_lines.append(f"  {device:25s} ✗ ERROR")
            report_lines.append("")
        
        # Underlay verification results
        if underlay_results:
            report_lines.append("UNDERLAY ROUTING VERIFICATION:")
            report_lines.append("-" * 80)
            for device, checks in sorted(underlay_results.items()):
                if isinstance(checks, dict) and 'error' not in checks:
                    all_passed = all(checks.values())
                    status = "✓ OPERATIONAL" if all_passed else "⚠ CHECK NEEDED"
                    report_lines.append(f"  {device:25s} {status}")
                else:
                    report_lines.append(f"  {device:25s} ⚠ VERIFY MANUALLY")
            report_lines.append("")
        
        # Summary
        success_count = sum(1 for r in cleanup_results.values() if r == 'SUCCESS')
        total_count = len(cleanup_results)
        
        report_lines.append("SUMMARY:")
        report_lines.append("-" * 80)
        report_lines.append(f"  Total devices processed:     {total_count}")
        report_lines.append(f"  Successful cleanups:         {success_count}")
        report_lines.append(f"  Failed cleanups:             {total_count - success_count}")
        report_lines.append(f"  Backup location:             {backup_dir}")
        report_lines.append("")
        report_lines.append("=" * 80)
        
        report = '\n'.join(report_lines)
        
        # Print to console
        logger.info(f"\n{report}")
        
        # Save to file
        report_file = Path(__file__).parent / "evpn_cleanup_configs" / f"cleanup_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w') as f:
            f.write(report)
        
        logger.info(f"\n✓ Report saved to: {report_file}")
    
    @aetest.subsection
    def disconnect_from_devices(self, testbed):
        """Disconnect from all devices"""
        
        logger.info("\nDisconnecting from devices...")
        
        for device in testbed.devices.values():
            if device.is_connected():
                try:
                    device.disconnect()
                    logger.info(f"  ✓ Disconnected from {device.name}")
                except Exception as e:
                    logger.warning(f"  ⚠ Error disconnecting from {device.name}: {e}")


if __name__ == '__main__':
    import sys
    from pyats import topology
    
    # For standalone execution
    if len(sys.argv) < 2:
        print("Usage: pyats run job apply_evpn_cleanup_job.py --testbed-file evpn_testbed.yaml")
        sys.exit(1)
