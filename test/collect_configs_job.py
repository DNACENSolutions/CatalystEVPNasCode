#!/usr/bin/env python3
"""
PyATS Job File for Device Configuration Collection

This job file orchestrates the execution of the device configuration collection script.
It provides better control over test execution, reporting, and scheduling.

By default, the script collects configurations from core infrastructure devices only:
    - Switches: TB16-Fusion, TB16-Spine
    - Border Nodes: TB16-SJ-BORDER-1, TB16-SJ-BORDER-2, TB16-SJ-Border-3, TB16-NY-Border
    - Leaf Switches: TB16-SJ-Leaf-1, TB16-SJ-Leaf-2, TB16-SJ-Leaf-3, TB16-NY-Leaf
    - Wireless Controllers: TB16-eWLC-1, TB16-eWLC-2

Excluded devices (APs, sensors, ISE, external nodes, clients) are automatically skipped.

Usage:
    # Collect from core infrastructure devices (default)
    pyats run job collect_configs_job.py --testbed-file evpn_testbed.yaml
    
    # Collect from specific devices only
    pyats run job collect_configs_job.py --testbed-file evpn_testbed.yaml --devices TB16-Fusion,TB16-SJ-BORDER-1
    
    # Custom output directory
    pyats run job collect_configs_job.py --testbed-file evpn_testbed.yaml --output-dir /tmp/configs
    
    # With email notification
    pyats run job collect_configs_job.py --testbed-file evpn_testbed.yaml --mail-to admin@example.com
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path

# PyATS imports
from pyats.easypy import run
from pyats.datastructures.logic import And, Or, Not

# Configure logging
logger = logging.getLogger(__name__)


def main(runtime):
    """
    Main job function that orchestrates the configuration collection
    
    Args:
        runtime: PyATS runtime object containing job parameters
    """
    
    # Get custom arguments from command line
    custom_args = runtime.args
    
    # Determine output directory
    output_dir = getattr(custom_args, 'output_dir', './device_configs')
    
    # Determine device list
    device_list = None
    if hasattr(custom_args, 'devices') and custom_args.devices:
        device_list = custom_args.devices.split(',')
        logger.info(f"Job will collect from specific devices: {device_list}")
    else:
        logger.info("Job will collect from all network devices")
    
    # Log job start
    logger.info("=" * 80)
    logger.info("EVPN Device Configuration Collection Job")
    logger.info("=" * 80)
    logger.info(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Testbed: {runtime.testbed.name}")
    logger.info(f"Output Directory: {output_dir}")
    logger.info(f"Archive Directory: {runtime.directory}")
    logger.info("=" * 80)
    
    # Run the configuration collection script
    run(
        testscript='collect_device_configs.py',
        runtime=runtime,
        taskid='ConfigCollection',
        device_list=device_list,
        output_dir=output_dir
    )
    
    # Log job completion
    logger.info("=" * 80)
    logger.info("Job Completed")
    logger.info(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Results: {runtime.directory}")
    logger.info("=" * 80)


# Custom argument parser for additional job parameters
def custom_args(parser):
    """
    Add custom arguments to the job parser
    
    Args:
        parser: ArgumentParser object
    """
    
    parser.add_argument(
        '--devices',
        type=str,
        default=None,
        help='Comma-separated list of device names to collect from'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='./device_configs',
        help='Output directory for collected configurations'
    )
    
    parser.add_argument(
        '--mail-to',
        type=str,
        default=None,
        help='Email address to send job results to'
    )
    
    parser.add_argument(
        '--mail-subject',
        type=str,
        default='EVPN Config Collection Results',
        help='Email subject line'
    )


if __name__ == '__main__':
    import sys
    print("This is a PyATS job file. Please run it using:")
    print("  pyats run job collect_configs_job.py --testbed-file evpn_testbed.yaml")
    sys.exit(1)
