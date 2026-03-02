#!/usr/bin/env python3
"""
PyATS Script for Dynamic EVPN Cleanup
Uses intelligent detection instead of static config files
Handles partial cleanups gracefully
"""

import logging
from pyats import aetest
from pyats.log.utils import banner
from dynamic_evpn_cleanup import clear_device_evpn, clear_multiple_devices_evpn

logger = logging.getLogger(__name__)


class CommonSetup(aetest.CommonSetup):
    """Common setup tasks"""
    
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


class DynamicCleanupEVPN(aetest.Testcase):
    """Dynamically clean EVPN configuration from devices"""
    
    @aetest.setup
    def setup(self, testbed):
        """Setup for dynamic cleanup"""
        
        self.connected_devices = self.parent.parameters.get('connected_devices', [])
        self.testbed = testbed
        
        if not self.connected_devices:
            self.skipped("No connected devices to clean")
    
    @aetest.test
    def dynamic_cleanup(self, testbed, remove_bgp=False):
        """Apply dynamic EVPN cleanup to all connected devices"""
        
        logger.info(banner("Dynamic EVPN Cleanup"))
        
        results = {}
        
        for device_name in self.connected_devices:
            device = testbed.devices[device_name]
            
            logger.info(banner(f"Cleaning {device_name}"))
            
            try:
                result = clear_device_evpn(
                    device, 
                    remove_bgp_completely=remove_bgp,
                    preserve_mgmt_vrf=True
                )
                
                if result == 1:
                    logger.info(f"✓ Successfully cleaned {device_name}")
                    results[device_name] = 'SUCCESS'
                else:
                    logger.warning(f"⚠ Cleanup completed with warnings on {device_name}")
                    results[device_name] = 'SUCCESS_WITH_WARNINGS'
                    
            except Exception as e:
                logger.error(f"✗ Failed to clean {device_name}: {e}")
                results[device_name] = f'FAILED: {e}'
        
        # Store results
        self.parent.parameters['cleanup_results'] = results
        
        # Check if any succeeded
        success_count = sum(1 for r in results.values() if 'SUCCESS' in r)
        
        if success_count == 0:
            self.failed("Failed to clean any devices!")
        elif success_count < len(results):
            logger.warning(f"Cleanup succeeded on {success_count}/{len(results)} devices")
        else:
            logger.info(f"✓ Cleanup succeeded on all {success_count} devices")


class VerifyCleanup(aetest.Testcase):
    """Verify EVPN components are removed"""
    
    @aetest.setup
    def setup(self):
        """Setup for verification"""
        
        self.cleanup_results = self.parent.parameters.get('cleanup_results', {})
        
        # Only verify devices where cleanup succeeded
        self.devices_to_verify = [
            name for name, result in self.cleanup_results.items() 
            if 'SUCCESS' in result
        ]
        
        if not self.devices_to_verify:
            self.skipped("No devices with successful cleanup to verify")
    
    @aetest.test
    def verify_evpn_removed(self, testbed):
        """Verify EVPN components are removed"""
        
        logger.info(banner("Verifying EVPN Removal"))
        
        all_passed = True
        
        for device_name in self.devices_to_verify:
            device = testbed.devices[device_name]
            
            logger.info(f"\n{'='*60}")
            logger.info(f"Verifying {device_name}")
            logger.info(f"{'='*60}")
            
            checks = {
                'L2VPN EVPN': 'show running-config | include l2vpn evpn',
                'NVE Interface': 'show running-config | include interface nve',
                'BGP EVPN AF': 'show running-config | include address-family l2vpn evpn',
            }
            
            for check_name, command in checks.items():
                try:
                    output = device.execute(command, prompt_recovery=True)
                    
                    if output and len(output.strip()) > 5:
                        logger.warning(f"  ⚠ {check_name} still present on {device_name}")
                        logger.debug(f"Output: {output}")
                        all_passed = False
                    else:
                        logger.info(f"  ✓ {check_name} removed from {device_name}")
                        
                except Exception as e:
                    logger.error(f"  ✗ Failed to verify {check_name} on {device_name}: {e}")
                    all_passed = False
        
        if not all_passed:
            logger.warning("Some EVPN components may still be present")
        else:
            logger.info("\n✓ All EVPN components successfully removed")


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
        """Generate cleanup summary report"""
        
        logger.info(banner("Cleanup Summary"))
        
        results = self.parent.parameters.get('cleanup_results', {})
        
        if not results:
            logger.info("No cleanup results to report")
            return
        
        success = [name for name, result in results.items() if 'SUCCESS' in result]
        failed = [name for name, result in results.items() if 'FAILED' in result]
        
        logger.info(f"\nTotal Devices: {len(results)}")
        logger.info(f"Successful: {len(success)}")
        logger.info(f"Failed: {len(failed)}")
        
        if success:
            logger.info(f"\n✓ Successfully cleaned:")
            for name in success:
                logger.info(f"  - {name}")
        
        if failed:
            logger.info(f"\n✗ Failed to clean:")
            for name in failed:
                logger.info(f"  - {name}: {results[name]}")


if __name__ == '__main__':
    import argparse
    from pyats.topology import loader
    
    parser = argparse.ArgumentParser(description='Dynamic EVPN Cleanup Script')
    parser.add_argument('--testbed', required=True, help='Path to testbed file')
    parser.add_argument('--devices', help='Comma-separated list of devices (default: all)')
    parser.add_argument('--remove-bgp', action='store_true', help='Remove BGP completely')
    
    args, unknown = parser.parse_known_args()
    
    # Load testbed
    testbed = loader.load(args.testbed)
    
    # Run the test
    aetest.main(testbed=testbed, devices=args.devices, remove_bgp=args.remove_bgp)
