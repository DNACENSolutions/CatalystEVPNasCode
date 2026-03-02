#!/bin/bash
################################################################################
# Scheduled EVPN Device Configuration Collection
#
# This script is designed to be run via cron or systemd timer for automated
# configuration backups. It includes logging, error handling, and cleanup.
#
# Cron Example (Daily at 2 AM):
#   0 2 * * * /path/to/scheduled_config_collection.sh
#
# Cron Example (Every 6 hours):
#   0 */6 * * * /path/to/scheduled_config_collection.sh
################################################################################

# Configuration
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
TESTBED_FILE="$SCRIPT_DIR/evpn_testbed.yaml"
OUTPUT_BASE_DIR="$SCRIPT_DIR/device_configs"
LOG_DIR="$SCRIPT_DIR/logs"
RETENTION_DAYS=30  # Keep backups for 30 days
MAX_BACKUPS=50     # Maximum number of backup directories to keep

# Email configuration (optional)
SEND_EMAIL=false
EMAIL_TO=""
EMAIL_FROM="evpn-backup@example.com"
EMAIL_SUBJECT="EVPN Config Collection Report"

# Logging setup
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$LOG_DIR/config_collection_${TIMESTAMP}.log"

# Create directories
mkdir -p "$LOG_DIR"
mkdir -p "$OUTPUT_BASE_DIR"

# Redirect all output to log file
exec 1> >(tee -a "$LOG_FILE")
exec 2>&1

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" >&2
}

log_success() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] SUCCESS: $1"
}

# Function to send email notification
send_email() {
    local subject="$1"
    local body="$2"
    
    if [ "$SEND_EMAIL" = true ] && [ -n "$EMAIL_TO" ]; then
        if command -v mail &> /dev/null; then
            echo "$body" | mail -s "$subject" -r "$EMAIL_FROM" "$EMAIL_TO"
            log "Email notification sent to $EMAIL_TO"
        else
            log_error "mail command not found, cannot send email"
        fi
    fi
}

# Function to cleanup old backups
cleanup_old_backups() {
    log "Cleaning up old backups..."
    
    # Remove backups older than RETENTION_DAYS
    if [ -d "$OUTPUT_BASE_DIR" ]; then
        find "$OUTPUT_BASE_DIR" -maxdepth 1 -type d -name "20*" -mtime +${RETENTION_DAYS} -exec rm -rf {} \;
        log "Removed backups older than $RETENTION_DAYS days"
    fi
    
    # Keep only MAX_BACKUPS most recent backups
    BACKUP_COUNT=$(find "$OUTPUT_BASE_DIR" -maxdepth 1 -type d -name "20*" | wc -l)
    if [ $BACKUP_COUNT -gt $MAX_BACKUPS ]; then
        BACKUPS_TO_DELETE=$((BACKUP_COUNT - MAX_BACKUPS))
        find "$OUTPUT_BASE_DIR" -maxdepth 1 -type d -name "20*" | sort | head -n $BACKUPS_TO_DELETE | xargs rm -rf
        log "Removed $BACKUPS_TO_DELETE old backups to maintain limit of $MAX_BACKUPS"
    fi
}

# Function to cleanup old logs
cleanup_old_logs() {
    log "Cleaning up old logs..."
    
    if [ -d "$LOG_DIR" ]; then
        find "$LOG_DIR" -name "config_collection_*.log" -mtime +${RETENTION_DAYS} -delete
        log "Removed logs older than $RETENTION_DAYS days"
    fi
}

# Start
log "================================================================================"
log "EVPN Scheduled Configuration Collection Started"
log "================================================================================"
log "Timestamp: $TIMESTAMP"
log "Testbed: $TESTBED_FILE"
log "Output Directory: $OUTPUT_BASE_DIR"
log "Log File: $LOG_FILE"

# Check if testbed file exists
if [ ! -f "$TESTBED_FILE" ]; then
    log_error "Testbed file not found: $TESTBED_FILE"
    send_email "FAILED: $EMAIL_SUBJECT" "Testbed file not found: $TESTBED_FILE"
    exit 1
fi

# Check if PyATS is installed
if ! command -v pyats &> /dev/null; then
    log_error "PyATS is not installed"
    send_email "FAILED: $EMAIL_SUBJECT" "PyATS is not installed on the system"
    exit 1
fi

log "PyATS version: $(pyats version | head -1)"

# Change to script directory
cd "$SCRIPT_DIR"

# Run the configuration collection
log "Starting configuration collection..."
START_TIME=$(date +%s)

pyats run job collect_configs_job.py \
    --testbed-file "$TESTBED_FILE" \
    --output-dir "$OUTPUT_BASE_DIR" \
    >> "$LOG_FILE" 2>&1

EXIT_CODE=$?
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

log "Configuration collection completed with exit code: $EXIT_CODE"
log "Duration: ${DURATION} seconds"

# Find the latest output directory
LATEST_DIR=$(find "$OUTPUT_BASE_DIR" -maxdepth 1 -type d -name "20*" | sort -r | head -1)

if [ $EXIT_CODE -eq 0 ]; then
    log_success "Configuration collection completed successfully"
    
    if [ -n "$LATEST_DIR" ]; then
        # Count collected files
        RUNNING_CONFIGS=$(find "$LATEST_DIR/running_configs" -type f 2>/dev/null | wc -l)
        STARTUP_CONFIGS=$(find "$LATEST_DIR/startup_configs" -type f 2>/dev/null | wc -l)
        DEVICE_INFOS=$(find "$LATEST_DIR/device_info" -type f 2>/dev/null | wc -l)
        
        log "Results saved to: $LATEST_DIR"
        log "Collected Files:"
        log "  - Running Configs: $RUNNING_CONFIGS"
        log "  - Startup Configs: $STARTUP_CONFIGS"
        log "  - Device Info: $DEVICE_INFOS"
        
        # Create archive
        log "Creating compressed archive..."
        ARCHIVE_NAME="evpn_configs_${TIMESTAMP}.tar.gz"
        tar -czf "$OUTPUT_BASE_DIR/$ARCHIVE_NAME" -C "$OUTPUT_BASE_DIR" "$(basename $LATEST_DIR)" 2>&1
        
        if [ $? -eq 0 ]; then
            ARCHIVE_SIZE=$(du -h "$OUTPUT_BASE_DIR/$ARCHIVE_NAME" | cut -f1)
            log_success "Archive created: $ARCHIVE_NAME ($ARCHIVE_SIZE)"
            
            # Prepare email body
            EMAIL_BODY="EVPN Configuration Collection Report

Status: SUCCESS
Timestamp: $(date '+%Y-%m-%d %H:%M:%S')
Duration: ${DURATION} seconds

Collected Files:
- Running Configs: $RUNNING_CONFIGS
- Startup Configs: $STARTUP_CONFIGS
- Device Info: $DEVICE_INFOS

Output Directory: $LATEST_DIR
Archive: $OUTPUT_BASE_DIR/$ARCHIVE_NAME ($ARCHIVE_SIZE)

Log File: $LOG_FILE
"
            send_email "SUCCESS: $EMAIL_SUBJECT" "$EMAIL_BODY"
        else
            log_error "Failed to create archive"
        fi
    fi
    
    # Cleanup old backups and logs
    cleanup_old_backups
    cleanup_old_logs
    
else
    log_error "Configuration collection failed"
    
    # Prepare failure email
    EMAIL_BODY="EVPN Configuration Collection Report

Status: FAILED
Timestamp: $(date '+%Y-%m-%d %H:%M:%S')
Duration: ${DURATION} seconds
Exit Code: $EXIT_CODE

Please check the log file for details:
$LOG_FILE
"
    send_email "FAILED: $EMAIL_SUBJECT" "$EMAIL_BODY"
fi

log "================================================================================"
log "EVPN Scheduled Configuration Collection Finished"
log "================================================================================"

exit $EXIT_CODE
