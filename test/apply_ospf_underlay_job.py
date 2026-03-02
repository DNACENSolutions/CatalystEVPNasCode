#!/usr/bin/env python3
"""
PyATS Job File for OSPF Underlay Application
Orchestrates the OSPF underlay script execution
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
    dry_run = getattr(runtime.args, 'dry_run', False)
    ospf_config_dir = getattr(runtime.args, 'ospf_config_dir', 'ospf_underlay_configs')
    
    # Log job information
    logger.info("="*70)
    logger.info("OSPF Underlay Application Job")
    logger.info("="*70)
    logger.info(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Testbed: {runtime.testbed.name}")
    
    if devices:
        logger.info(f"Target Devices: {devices}")
    else:
        logger.info("Target Devices: ALL (except BASE-DEVICE)")
    
    logger.info(f"Dry Run Mode: {dry_run}")
    logger.info(f"OSPF Config Directory: {ospf_config_dir}")
    logger.info("="*70)
    
    # Run the OSPF application script
    run(
        testscript='apply_ospf_underlay.py',
        runtime=runtime,
        testbed=runtime.testbed,
        devices=devices,
        dry_run=dry_run,
        ospf_config_dir=ospf_config_dir
    )
    
    logger.info("="*70)
    logger.info(f"Job completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*70)
