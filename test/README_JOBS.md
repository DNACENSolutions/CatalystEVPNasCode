# EVPN Configuration Collection Jobs

This directory contains PyATS jobs and scripts for automated device configuration collection from the EVPN testbed.

## Files Overview

| File | Purpose | Usage |
|------|---------|-------|
| `collect_configs_job.py` | PyATS job orchestrator | Run via `pyats run job` |
| `run_config_collection.sh` | Interactive wrapper script | Manual execution with options |
| `scheduled_config_collection.sh` | Automated backup script | Cron/systemd scheduling |
| `collect_device_configs.py` | Core PyATS test script | Called by job file |
| `evpn_testbed.yaml` | Device testbed definition | Connection details |

## Quick Start

### 1. Make Scripts Executable

```bash
chmod +x run_config_collection.sh
chmod +x scheduled_config_collection.sh
```

### 2. Run Interactive Collection

```bash
# Collect from all devices
./run_config_collection.sh

# Collect from specific devices
./run_config_collection.sh --devices TB16-Fusion,TB16-SJ-BORDER-1

# With custom output and archive
./run_config_collection.sh --output /backup/configs --archive
```

## Usage Methods

### Method 1: PyATS Job (Recommended)

Direct PyATS job execution with full reporting and logging.

```bash
# Basic usage
pyats run job collect_configs_job.py --testbed-file evpn_testbed.yaml

# Specific devices
pyats run job collect_configs_job.py \
    --testbed-file evpn_testbed.yaml \
    --devices TB16-Fusion,TB16-SJ-BORDER-1,TB16-SJ-Leaf-1

# Custom output directory
pyats run job collect_configs_job.py \
    --testbed-file evpn_testbed.yaml \
    --output-dir /tmp/evpn_backups

# With email notification
pyats run job collect_configs_job.py \
    --testbed-file evpn_testbed.yaml \
    --mail-to admin@example.com
```

**Output Location:**
- PyATS creates a unique archive directory: `~/.pyats/archive/<timestamp>/`
- Configuration files: `<output-dir>/<timestamp>/`

### Method 2: Shell Script Wrapper

User-friendly wrapper with colored output and additional features.

```bash
# Show help
./run_config_collection.sh --help

# Basic collection
./run_config_collection.sh

# Specific devices
./run_config_collection.sh --devices TB16-Fusion,TB16-SJ-BORDER-1

# Custom output directory
./run_config_collection.sh --output /backup/configs

# Create tar.gz archive
./run_config_collection.sh --archive

# With email notification
./run_config_collection.sh --email admin@cisco.com

# Combined options
./run_config_collection.sh \
    --devices TB16-Fusion,TB16-SJ-BORDER-1 \
    --output /backup/configs \
    --archive \
    --email admin@cisco.com
```

**Features:**
- ✅ Colored console output
- ✅ Progress indicators
- ✅ Summary statistics
- ✅ Automatic archiving option
- ✅ Email notifications

### Method 3: Scheduled Execution

Automated backups via cron or systemd timer.

#### Cron Setup

```bash
# Edit crontab
crontab -e

# Add one of these lines:

# Daily at 2 AM
0 2 * * * /path/to/scheduled_config_collection.sh

# Every 6 hours
0 */6 * * * /path/to/scheduled_config_collection.sh

# Weekly on Sunday at 3 AM
0 3 * * 0 /path/to/scheduled_config_collection.sh

# Every weekday at 1 AM
0 1 * * 1-5 /path/to/scheduled_config_collection.sh
```

#### Configuration

Edit `scheduled_config_collection.sh` to configure:

```bash
# Retention settings
RETENTION_DAYS=30      # Keep backups for 30 days
MAX_BACKUPS=50         # Maximum number of backups

# Email notifications
SEND_EMAIL=true
EMAIL_TO="admin@example.com"
EMAIL_FROM="evpn-backup@example.com"
```

**Features:**
- ✅ Automatic cleanup of old backups
- ✅ Automatic log rotation
- ✅ Email notifications on success/failure
- ✅ Compressed archives
- ✅ Detailed logging

## Output Structure

All methods produce the same output structure:

```
device_configs/
├── 20260205_153000/              # Timestamped directory
│   ├── SUMMARY.txt               # Collection summary
│   ├── running_configs/
│   │   ├── TB16-Fusion_running.cfg
│   │   ├── TB16-SJ-BORDER-1_running.cfg
│   │   └── ...
│   ├── startup_configs/
│   │   ├── TB16-Fusion_startup.cfg
│   │   └── ...
│   └── device_info/
│       ├── TB16-Fusion_info.txt
│       └── ...
└── evpn_configs_20260205_153000.tar.gz  # Optional archive
```

## Device Selection

### Collect from All Network Devices

```bash
# Automatically excludes clients, servers, Ixia
./run_config_collection.sh
```

### Collect from Specific Devices

```bash
# Border nodes only
./run_config_collection.sh --devices TB16-SJ-BORDER-1,TB16-SJ-BORDER-2,TB16-NY-Border

# Leaf switches only
./run_config_collection.sh --devices TB16-SJ-Leaf-1,TB16-SJ-Leaf-2,TB16-SJ-Leaf-3

# Core infrastructure
./run_config_collection.sh --devices TB16-Fusion,TB16-Spine

# Single device
./run_config_collection.sh --devices TB16-Fusion
```

## Advanced Usage

### Pre-Deployment Backup

```bash
# Backup before EVPN deployment
./run_config_collection.sh \
    --output ./backups/pre_deployment_$(date +%Y%m%d) \
    --archive \
    --email deployment-team@example.com
```

### Post-Deployment Verification

```bash
# Backup after deployment
./run_config_collection.sh \
    --output ./backups/post_deployment_$(date +%Y%m%d) \
    --archive

# Compare configurations
diff -r ./backups/pre_deployment_*/running_configs/ \
        ./backups/post_deployment_*/running_configs/
```

### Disaster Recovery Backup

```bash
# Full backup with archiving
./run_config_collection.sh \
    --output /mnt/backup/evpn_dr \
    --archive \
    --email dr-team@example.com
```

### Compliance Audit Collection

```bash
# Collect for audit purposes
./run_config_collection.sh \
    --output /audit/evpn_$(date +%Y%m%d) \
    --archive \
    --email compliance@example.com
```

## Troubleshooting

### Job Fails to Start

**Problem:** `pyats: command not found`

**Solution:**
```bash
# Install PyATS
pip install pyats genie unicon

# Or activate virtual environment
source /path/to/venv/bin/activate
```

### Connection Failures

**Problem:** Devices fail to connect

**Solutions:**
1. Verify testbed file credentials
2. Check network connectivity
3. Verify terminal server is accessible
4. Review PyATS logs in `~/.pyats/archive/`

### Console Clearing Issues

**Problem:** Devices stuck in config mode

**Solution:** The script automatically handles this with:
- Multiple Ctrl+C attempts
- Multiple 'end' commands
- Verification with 'show clock'
- Retry logic

### Permission Denied

**Problem:** Cannot write to output directory

**Solution:**
```bash
# Create directory with proper permissions
mkdir -p /path/to/output
chmod 755 /path/to/output

# Or use a different directory
./run_config_collection.sh --output ~/configs
```

### Email Not Sending

**Problem:** Email notifications not working

**Solutions:**
```bash
# Install mail utility (Ubuntu/Debian)
sudo apt-get install mailutils

# Install mail utility (RHEL/CentOS)
sudo yum install mailx

# Configure SMTP settings in /etc/mail.rc
```

## Logs and Reports

### PyATS Job Logs

```bash
# View latest job log
ls -lt ~/.pyats/archive/
cd ~/.pyats/archive/<latest>/

# Key files:
# - TaskLog.html - HTML report
# - runinfo/jobinfo.txt - Job information
# - runinfo/result_summary.txt - Results summary
```

### Scheduled Script Logs

```bash
# View logs
ls -lt logs/
tail -f logs/config_collection_*.log

# View latest log
tail -100 logs/$(ls -t logs/ | head -1)
```

### Collection Summary

```bash
# View summary from latest collection
cat device_configs/$(ls -t device_configs/ | grep ^20 | head -1)/SUMMARY.txt
```

## Integration Examples

### Ansible Playbook Integration

```yaml
- name: Collect device configurations
  command: >
    {{ playbook_dir }}/../test/run_config_collection.sh
    --output {{ backup_dir }}
    --archive
  register: config_collection

- name: Display collection results
  debug:
    var: config_collection.stdout_lines
```

### Python Script Integration

```python
import subprocess
import os

def collect_configs(output_dir, devices=None):
    """Collect device configurations"""
    
    cmd = [
        './run_config_collection.sh',
        '--output', output_dir,
        '--archive'
    ]
    
    if devices:
        cmd.extend(['--devices', ','.join(devices)])
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    return result.returncode == 0, result.stdout

# Usage
success, output = collect_configs(
    '/backup/evpn',
    devices=['TB16-Fusion', 'TB16-SJ-BORDER-1']
)
```

### Jenkins Pipeline Integration

```groovy
pipeline {
    agent any
    
    stages {
        stage('Collect Configs') {
            steps {
                sh '''
                    cd test
                    ./run_config_collection.sh \
                        --output ${WORKSPACE}/configs \
                        --archive \
                        --email ${BUILD_USER_EMAIL}
                '''
            }
        }
        
        stage('Archive Results') {
            steps {
                archiveArtifacts artifacts: 'configs/*.tar.gz'
            }
        }
    }
}
```

## Performance Considerations

### Collection Time

Typical collection times (per device):
- Running config: 5-10 seconds
- Startup config: 3-5 seconds
- Device info: 5-10 seconds
- **Total per device: ~15-25 seconds**

For 15 devices: **~5-7 minutes total**

### Optimization Tips

1. **Parallel collection** - PyATS handles device connections in parallel
2. **Specific devices** - Only collect from devices that changed
3. **Skip startup configs** - Modify script if not needed
4. **Network bandwidth** - Run from server close to devices

## Best Practices

### 1. Regular Backups

```bash
# Daily backups
0 2 * * * /path/to/scheduled_config_collection.sh

# Keep 30 days of backups
RETENTION_DAYS=30
```

### 2. Pre/Post Change Backups

```bash
# Before change
./run_config_collection.sh --output ./backups/pre_change --archive

# Make changes...

# After change
./run_config_collection.sh --output ./backups/post_change --archive
```

### 3. Version Control

```bash
# Initialize git repo for configs
cd device_configs
git init
git add .
git commit -m "Initial config backup"

# After each collection
git add .
git commit -m "Config backup $(date)"
```

### 4. Monitoring

```bash
# Check last backup status
tail -20 logs/$(ls -t logs/ | head -1)

# Alert if backup fails
if [ $? -ne 0 ]; then
    echo "Backup failed!" | mail -s "ALERT: Config Backup Failed" admin@example.com
fi
```

## Security Considerations

1. **Credentials** - Stored in testbed file, protect with proper permissions:
   ```bash
   chmod 600 evpn_testbed.yaml
   ```

2. **Output Files** - Contain sensitive configuration data:
   ```bash
   chmod 700 device_configs/
   ```

3. **Logs** - May contain sensitive information:
   ```bash
   chmod 700 logs/
   ```

4. **Archives** - Encrypt if storing off-site:
   ```bash
   gpg --encrypt evpn_configs_*.tar.gz
   ```

## Support

For issues or questions:
1. Check PyATS logs: `~/.pyats/archive/`
2. Check script logs: `./logs/`
3. Review testbed connectivity
4. Verify credentials and permissions

## Related Documentation

- [PyATS Documentation](https://developer.cisco.com/docs/pyats/)
- [Genie Documentation](https://developer.cisco.com/docs/genie-docs/)
- [Configuration Collection Script](./README_CONFIG_COLLECTION.md)
- [EVPN Deployment Guide](../README.md)
