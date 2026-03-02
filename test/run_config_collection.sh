#!/bin/bash
################################################################################
# EVPN Device Configuration Collection Runner
#
# This script provides an easy wrapper to run the PyATS configuration 
# collection job with common options.
#
# Usage:
#   ./run_config_collection.sh                          # Collect from all devices
#   ./run_config_collection.sh --devices TB16-Fusion    # Specific devices
#   ./run_config_collection.sh --output /tmp/configs    # Custom output dir
#   ./run_config_collection.sh --email admin@cisco.com  # Send email report
################################################################################

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Default values
TESTBED_FILE="evpn_testbed.yaml"
OUTPUT_DIR="./device_configs"
DEVICES=""
EMAIL=""
ARCHIVE=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored messages
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to display usage
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Options:
    -t, --testbed FILE          Testbed YAML file (default: evpn_testbed.yaml)
    -d, --devices DEVICES       Comma-separated device list (default: all)
    -o, --output DIR            Output directory (default: ./device_configs)
    -e, --email ADDRESS         Email address for results
    -a, --archive               Create tar.gz archive of results
    -h, --help                  Display this help message

Examples:
    # Collect from all devices
    $0

    # Collect from specific devices
    $0 --devices TB16-Fusion,TB16-SJ-BORDER-1

    # Custom output directory
    $0 --output /backup/configs

    # With email notification
    $0 --email admin@example.com

    # Archive results
    $0 --archive

    # Combined options
    $0 --devices TB16-Fusion --output /tmp/configs --email admin@cisco.com --archive

EOF
    exit 1
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--testbed)
            TESTBED_FILE="$2"
            shift 2
            ;;
        -d|--devices)
            DEVICES="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -e|--email)
            EMAIL="$2"
            shift 2
            ;;
        -a|--archive)
            ARCHIVE=true
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            print_error "Unknown option: $1"
            usage
            ;;
    esac
done

# Print banner
echo ""
echo "================================================================================"
echo "  EVPN Device Configuration Collection"
echo "================================================================================"
echo ""

# Check if testbed file exists
if [ ! -f "$TESTBED_FILE" ]; then
    print_error "Testbed file not found: $TESTBED_FILE"
    exit 1
fi

print_info "Testbed: $TESTBED_FILE"
print_info "Output Directory: $OUTPUT_DIR"

if [ -n "$DEVICES" ]; then
    print_info "Target Devices: $DEVICES"
else
    print_info "Target Devices: All network devices"
fi

if [ -n "$EMAIL" ]; then
    print_info "Email Report: $EMAIL"
fi

# Check if PyATS is installed
if ! command -v pyats &> /dev/null; then
    print_error "PyATS is not installed. Please install it first:"
    echo "  pip install pyats genie unicon"
    exit 1
fi

print_success "PyATS found: $(pyats version | head -1)"

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Build PyATS command
PYATS_CMD="pyats run job collect_configs_job.py --testbed-file $TESTBED_FILE --output-dir $OUTPUT_DIR"

if [ -n "$DEVICES" ]; then
    PYATS_CMD="$PYATS_CMD --devices $DEVICES"
fi

if [ -n "$EMAIL" ]; then
    PYATS_CMD="$PYATS_CMD --mail-to $EMAIL"
fi

# Display command
echo ""
print_info "Executing: $PYATS_CMD"
echo ""

# Run the job
START_TIME=$(date +%s)
$PYATS_CMD
EXIT_CODE=$?
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo ""
echo "================================================================================"

# Check exit code
if [ $EXIT_CODE -eq 0 ]; then
    print_success "Configuration collection completed successfully!"
    print_info "Duration: ${DURATION} seconds"
    
    # Find the latest output directory
    LATEST_DIR=$(find "$OUTPUT_DIR" -maxdepth 1 -type d -name "20*" | sort -r | head -1)
    
    if [ -n "$LATEST_DIR" ]; then
        print_info "Results saved to: $LATEST_DIR"
        
        # Count collected files
        RUNNING_CONFIGS=$(find "$LATEST_DIR/running_configs" -type f 2>/dev/null | wc -l)
        STARTUP_CONFIGS=$(find "$LATEST_DIR/startup_configs" -type f 2>/dev/null | wc -l)
        DEVICE_INFOS=$(find "$LATEST_DIR/device_info" -type f 2>/dev/null | wc -l)
        
        echo ""
        print_info "Collected Files:"
        echo "  - Running Configs: $RUNNING_CONFIGS"
        echo "  - Startup Configs: $STARTUP_CONFIGS"
        echo "  - Device Info: $DEVICE_INFOS"
        
        # Display summary if it exists
        if [ -f "$LATEST_DIR/SUMMARY.txt" ]; then
            echo ""
            print_info "Summary Report:"
            cat "$LATEST_DIR/SUMMARY.txt"
        fi
        
        # Create archive if requested
        if [ "$ARCHIVE" = true ]; then
            echo ""
            print_info "Creating archive..."
            ARCHIVE_NAME="evpn_configs_$(basename $LATEST_DIR).tar.gz"
            tar -czf "$OUTPUT_DIR/$ARCHIVE_NAME" -C "$OUTPUT_DIR" "$(basename $LATEST_DIR)"
            
            if [ $? -eq 0 ]; then
                ARCHIVE_SIZE=$(du -h "$OUTPUT_DIR/$ARCHIVE_NAME" | cut -f1)
                print_success "Archive created: $OUTPUT_DIR/$ARCHIVE_NAME ($ARCHIVE_SIZE)"
            else
                print_error "Failed to create archive"
            fi
        fi
    fi
else
    print_error "Configuration collection failed with exit code: $EXIT_CODE"
    print_info "Check the PyATS logs for details"
fi

echo "================================================================================"
echo ""

exit $EXIT_CODE
