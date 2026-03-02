#!/usr/bin/env python3
"""
PyATS Job File for Dynamic EVPN Cleanup
Orchestrates the dynamic cleanup script execution
"""

import os
import logging
from pyats.easypy import run
from datetime import datetime

logger = logging.getLogger(__name__)


def main(runtime):
    """
    Main job function
    """
    
    # Parse custom arguments
    devices = getattr(runtime.args, 'devices', None)
    remove_bgp = getattr(runtime.args, 'remove_bgp', False)
    
    # Log job information
    logger.info("="*70)
    logger.info("Dynamic EVPN Cleanup Job")
    logger.info("="*70)
    logger.info(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Testbed: {runtime.testbed.name}")
    
    if devices:
        logger.info(f"Target Devices: {devices}")
    else:
        logger.info("Target Devices: ALL (except BASE-DEVICE)")
    
    logger.info(f"Remove BGP Completely: {remove_bgp}")
    logger.info("="*70)
    
    # Run the dynamic cleanup script
    run(
        testscript='apply_dynamic_evpn_cleanup.py',
        runtime=runtime,
        testbed=runtime.testbed,
        devices=devices,
        remove_bgp=remove_bgp
    )
    
    logger.info("="*70)
    logger.info(f"Job completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*70)
