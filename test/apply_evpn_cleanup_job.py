#!/usr/bin/env python3
"""
PyATS Job File for EVPN Cleanup

This job file orchestrates the application of EVPN cleanup configurations
to remove BGP EVPN/VXLAN components from devices.

Usage:
    # Apply cleanup to all devices with cleanup configs
    pyats run job apply_evpn_cleanup_job.py --testbed-file evpn_testbed.yaml
    
    # Apply cleanup to specific devices only
    pyats run job apply_evpn_cleanup_job.py --testbed-file evpn_testbed.yaml \
        --devices TB16-SJ-Leaf-1 TB16-SJ-Leaf-2
    
    # Dry run (connect and verify but don't apply)
    pyats run job apply_evpn_cleanup_job.py --testbed-file evpn_testbed.yaml --dry-run
"""

import os
import logging
from pyats.easypy import run
from datetime import datetime

logger = logging.getLogger(__name__)


def main(runtime):
    """
    Main job function
    
    Arguments:
        runtime: PyATS runtime object containing job parameters
    """
    
    # Parse custom arguments from runtime.args (Namespace object)
    devices = getattr(runtime.args, 'devices', None)
    if devices and isinstance(devices, str):
        devices = [d.strip() for d in devices.split(',')]
    
    # Check for dry-run mode
    dry_run = getattr(runtime.args, 'dry_run', False)
    
    # Log job information
    logger.info("=" * 80)
    logger.info("EVPN CLEANUP JOB")
    logger.info("=" * 80)
    logger.info(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Testbed: {runtime.testbed.name}")
    logger.info(f"Testbed File: {runtime.testbed.testbed_file}")
    logger.info(f"Job Directory: {runtime.directory}")
    
    if devices:
        logger.info(f"Target Devices: {', '.join(devices)}")
    else:
        logger.info("Target Devices: All devices with cleanup configs")
    
    if dry_run:
        logger.info("Mode: DRY RUN (no changes will be applied)")
    else:
        logger.info("Mode: LIVE (cleanup will be applied)")
    
    logger.info("=" * 80)
    
    # Confirmation prompt for live runs
    if not dry_run:
        logger.warning("\n" + "!" * 80)
        logger.warning("WARNING: This will remove BGP EVPN/VXLAN configurations from devices!")
        logger.warning("!" * 80)
        logger.warning("\nWhat will be removed:")
        logger.warning("  - BGP EVPN address-families")
        logger.warning("  - NVE interfaces")
        logger.warning("  - L2VPN EVPN instances")
        logger.warning("  - EVPN VRFs and VLANs")
        logger.warning("  - SVI interfaces")
        logger.warning("\nWhat will be preserved:")
        logger.warning("  - ISIS routing protocol")
        logger.warning("  - OSPF routing protocol")
        logger.warning("  - Physical interfaces")
        logger.warning("  - Management VRF")
        logger.warning("  - Basic device configuration")
        logger.warning("\n" + "!" * 80)
        
        # In interactive mode, ask for confirmation
        if hasattr(runtime, 'interactive') and runtime.interactive:
            response = input("\nProceed with EVPN cleanup? (yes/no): ")
            if response.lower() != 'yes':
                logger.info("Cleanup cancelled by user")
                return
        else:
            logger.warning("\nNon-interactive mode: Proceeding with cleanup...")
            logger.warning("Use --dry-run flag to test without applying changes")
    
    # Run the cleanup script
    logger.info("\nStarting EVPN cleanup script...")
    
    run(
        testscript='apply_evpn_cleanup.py',
        runtime=runtime,
        testbed=runtime.testbed,
        devices=devices,
        dry_run=dry_run
    )
    
    logger.info("\n" + "=" * 80)
    logger.info("EVPN CLEANUP JOB COMPLETED")
    logger.info(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Results Directory: {runtime.directory}")
    logger.info("=" * 80)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='EVPN Cleanup Job')
    parser.add_argument('--testbed-file', required=True, help='Path to testbed YAML file')
    parser.add_argument('--devices', help='Comma-separated list of devices to clean (optional)')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode - no changes applied')
    
    args = parser.parse_args()
    
    print(f"Testbed file: {args.testbed_file}")
    if args.devices:
        print(f"Target devices: {args.devices}")
    if args.dry_run:
        print("Mode: DRY RUN")
