# Device Configuration Collection Script

This directory contains a PyATS script to collect device configurations from the EVPN testbed.

## Overview

The `collect_device_configs.py` script connects to network devices defined in the testbed file and collects:
- **Running configurations** - Current active configuration
- **Startup configurations** - Saved configuration (IOS/IOS-XE devices)
- **Device information** - Version, inventory, interface status

## Prerequisites

### Required Python Packages

```bash
pip install pyats genie unicon
```

### Testbed File

The script uses `evpn_testbed.yaml` which defines:
- Device connection details (IP, port, credentials)
- Device types and roles
- Network topology

## Usage

### Basic Usage - Collect from All Network Devices

```bash
cd /Users/pawansi/workspace/CatC_BGP_EVPNacCode/CatalystEVPNasCode/test
python collect_device_configs.py --testbed evpn_testbed.yaml
```

This will:
1. Connect to all network devices (switches, routers, WLCs)
2. Skip non-network devices (clients, servers, Ixia)
3. Collect configurations and device info
4. Save to `./device_configs/<timestamp>/`

### Collect from Specific Devices

```bash
python collect_device_configs.py --testbed evpn_testbed.yaml \
    --devices TB16-Fusion,TB16-SJ-BORDER-1,TB16-SJ-BORDER-2
```

### Specify Custom Output Directory

```bash
python collect_device_configs.py --testbed evpn_testbed.yaml \
    --output-dir /tmp/evpn_configs
```

### Get Help

```bash
python collect_device_configs.py --help
```

## Output Structure

The script creates a timestamped directory with the following structure:

```
device_configs/
└── 20260205_153000/
    ├── SUMMARY.txt                    # Collection summary report
    ├── running_configs/
    │   ├── TB16-Fusion_running.cfg
    │   ├── TB16-SJ-BORDER-1_running.cfg
    │   └── ...
    ├── startup_configs/
    │   ├── TB16-Fusion_startup.cfg
    │   ├── TB16-SJ-BORDER-1_startup.cfg
    │   └── ...
    └── device_info/
        ├── TB16-Fusion_info.txt
        ├── TB16-SJ-BORDER-1_info.txt
        └── ...
```

### File Contents

**Running Configs** (`running_configs/`)
- Full `show running-config` output
- Current active configuration
- All devices

**Startup Configs** (`startup_configs/`)
- Full `show startup-config` output
- Saved configuration in NVRAM
- IOS/IOS-XE devices only

**Device Info** (`device_info/`)
- Device name, type, OS, role
- `show version` output
- `show inventory` output
- `show ip interface brief` output

**Summary** (`SUMMARY.txt`)
- Collection timestamp
- Successfully connected devices
- Failed connections with error messages
- List of all collected files

## Supported Device Types

The script automatically handles different device types:

| Device Type | Running Config | Startup Config | Device Info |
|------------|----------------|----------------|-------------|
| IOS-XE (Switches, Routers) | ✓ | ✓ | ✓ |
| IOS (Legacy devices) | ✓ | ✓ | ✓ |
| AireOS (WLCs, APs) | ✓ | - | Limited |
| ISE | ✓ | - | Limited |

## Example Output

### Console Output

```
2026-02-05 15:30:00 - INFO - Loading testbed from: evpn_testbed.yaml
2026-02-05 15:30:01 - INFO - Loaded testbed: SanityTB8
2026-02-05 15:30:01 - INFO - Total devices in testbed: 45
2026-02-05 15:30:01 - INFO - Attempting to connect to 15 devices
2026-02-05 15:30:02 - INFO - Connecting to TB16-Fusion...
2026-02-05 15:30:05 - INFO - Successfully connected to TB16-Fusion
2026-02-05 15:30:05 - INFO - Connecting to TB16-SJ-BORDER-1...
2026-02-05 15:30:08 - INFO - Successfully connected to TB16-SJ-BORDER-1
...
2026-02-05 15:35:00 - INFO - Connected to 15 devices
2026-02-05 15:35:00 - INFO - Configurations will be saved to: ./device_configs/20260205_153000
2026-02-05 15:35:00 - INFO - Collecting running config from TB16-Fusion...
2026-02-05 15:35:02 - INFO - Saved running config for TB16-Fusion (45678 bytes)
...
```

### Summary Report Example

```
================================================================================
DEVICE CONFIGURATION COLLECTION SUMMARY
================================================================================
Collection Time: 2026-02-05 15:35:30
Output Directory: ./device_configs/20260205_153000

Successfully Connected Devices: 15
  - TB16-Fusion (IOS-XE)
  - TB16-SJ-BORDER-1 (IOS-XE)
  - TB16-SJ-BORDER-2 (IOS-XE)
  - TB16-SJ-Leaf-1 (IOS-XE)
  - TB16-SJ-Leaf-2 (IOS-XE)
  ...

Failed to Connect: 2
  - TB16-eWLC-2: Connection timeout
  - TB16-NY-Leaf: Authentication failed

================================================================================
FILES COLLECTED:
================================================================================
Running Configurations: 15
  - TB16-Fusion_running.cfg
  - TB16-SJ-BORDER-1_running.cfg
  ...

Startup Configurations: 15
  - TB16-Fusion_startup.cfg
  - TB16-SJ-BORDER-1_startup.cfg
  ...

Device Information Files: 15
  - TB16-Fusion_info.txt
  - TB16-SJ-BORDER-1_info.txt
  ...
================================================================================
```

## Troubleshooting

### Connection Issues

**Problem**: `Failed to connect to device: Connection timeout`

**Solutions**:
- Verify device is reachable: `ping <device_ip>`
- Check terminal server is accessible
- Verify port numbers in testbed file
- Check firewall rules

**Problem**: `Authentication failed`

**Solutions**:
- Verify credentials in testbed file
- Check username/password are correct
- Ensure enable password is set
- Try connecting manually via telnet/ssh

### Permission Issues

**Problem**: `Permission denied` when saving files

**Solutions**:
```bash
# Create output directory with proper permissions
mkdir -p device_configs
chmod 755 device_configs

# Or specify a different output directory
python collect_device_configs.py --testbed evpn_testbed.yaml --output-dir /tmp/configs
```

### PyATS/Genie Issues

**Problem**: `ModuleNotFoundError: No module named 'pyats'`

**Solution**:
```bash
# Install PyATS and Genie
pip install pyats genie unicon

# Or use virtual environment
python3 -m venv venv
source venv/bin/activate
pip install pyats genie unicon
```

## Integration with EVPN Deployment

This script can be used as part of the EVPN deployment workflow:

### Pre-Deployment Configuration Backup

```bash
# Backup configs before deployment
python collect_device_configs.py --testbed evpn_testbed.yaml \
    --output-dir ./backups/pre_deployment
```

### Post-Deployment Verification

```bash
# Collect configs after deployment
python collect_device_configs.py --testbed evpn_testbed.yaml \
    --output-dir ./backups/post_deployment

# Compare configurations
diff -r ./backups/pre_deployment/running_configs/ \
        ./backups/post_deployment/running_configs/
```

### Specific Device Group Collection

```bash
# Collect only from border nodes
python collect_device_configs.py --testbed evpn_testbed.yaml \
    --devices TB16-SJ-BORDER-1,TB16-SJ-BORDER-2,TB16-NY-Border

# Collect only from leaf switches
python collect_device_configs.py --testbed evpn_testbed.yaml \
    --devices TB16-SJ-Leaf-1,TB16-SJ-Leaf-2,TB16-SJ-Leaf-3,TB16-NY-Leaf
```

## Advanced Usage

### Scheduled Collection with Cron

```bash
# Add to crontab for daily collection at 2 AM
0 2 * * * cd /path/to/test && python collect_device_configs.py --testbed evpn_testbed.yaml --output-dir /backups/daily
```

### Collection Script in Ansible Playbook

```yaml
- name: Collect device configurations using PyATS
  command: >
    python /path/to/test/collect_device_configs.py
    --testbed /path/to/test/evpn_testbed.yaml
    --output-dir /tmp/configs
  register: config_collection
  
- name: Display collection summary
  debug:
    msg: "{{ config_collection.stdout }}"
```

## Script Architecture

The script uses PyATS framework with the following structure:

1. **CommonSetup**: Connect to devices
2. **CollectConfigurations**: Main test case
   - `collect_running_config`: Get running configs
   - `collect_startup_config`: Get startup configs
   - `collect_device_info`: Get device information
   - `generate_summary`: Create summary report
3. **CommonCleanup**: Disconnect from devices

## Related Files

- `evpn_testbed.yaml` - Testbed definition file
- `../playbooks/evpn_deployment.yml` - EVPN deployment playbook
- `../data/bgp_evpn_templates_*.yaml` - Template configuration files

## Support

For issues or questions:
1. Check the SUMMARY.txt file for connection errors
2. Review PyATS logs in the output directory
3. Verify testbed file syntax and credentials
4. Test manual connection to devices

## References

- [PyATS Documentation](https://developer.cisco.com/docs/pyats/)
- [Genie Documentation](https://developer.cisco.com/docs/genie-docs/)
- [Unicon Documentation](https://developer.cisco.com/docs/unicon/)
