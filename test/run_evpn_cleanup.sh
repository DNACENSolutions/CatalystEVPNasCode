#!/bin/bash
#
# EVPN Cleanup Execution Script
#
# This script provides an easy interface to run the PyATS EVPN cleanup job
# that removes BGP EVPN/VXLAN configurations from devices.
#
# Usage:
#   ./run_evpn_cleanup.sh                    # Clean all devices (interactive)
#   ./run_evpn_cleanup.sh --devices leaf1    # Clean specific device
#   ./run_evpn_cleanup.sh --dry-run          # Test without applying
#   ./run_evpn_cleanup.sh --help             # Show help
#

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
TESTBED_FILE="${SCRIPT_DIR}/evpn_testbed.yaml"
CLEANUP_DIR="${SCRIPT_DIR}/evpn_cleanup_configs"
LOG_DIR="${SCRIPT_DIR}/cleanup_logs"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Default values
DEVICES=""
DRY_RUN=false
INTERACTIVE=true
ARCHIVE=true

# Function to print colored output
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

# Function to show usage
show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

EVPN Cleanup Script - Remove BGP EVPN/VXLAN configurations from devices

OPTIONS:
    --devices DEVICE_LIST   Comma-separated list of devices to clean
                           Example: --devices TB16-SJ-Leaf-1,TB16-SJ-Leaf-2
    
    --dry-run              Run in dry-run mode (no changes applied)
    
    --non-interactive      Run without prompts (use with caution!)
    
    --no-archive           Don't archive PyATS results
    
    --testbed FILE         Use custom testbed file (default: evpn_testbed.yaml)
    
    --help                 Show this help message

EXAMPLES:
    # Clean all devices with interactive confirmation
    $0
    
    # Clean specific devices
    $0 --devices TB16-SJ-Leaf-1,TB16-SJ-Leaf-2
    
    # Dry run to test without applying changes
    $0 --dry-run
    
    # Non-interactive mode (for automation)
    $0 --devices TB16-SJ-Leaf-1 --non-interactive

WHAT GETS REMOVED:
    ✗ BGP EVPN address-families (l2vpn evpn, ipv4 mvpn)
    ✗ NVE interfaces (nve1)
    ✗ L2VPN EVPN instances
    ✗ EVPN VRFs (red, blue, green)
    ✗ EVPN VLANs and SVI interfaces
    ✗ VRF multicast routing

WHAT GETS PRESERVED:
    ✓ ISIS routing protocol
    ✓ OSPF routing protocol
    ✓ Physical interfaces
    ✓ Management VRF
    ✓ AAA configuration
    ✓ Basic device settings

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --devices)
            DEVICES="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --non-interactive)
            INTERACTIVE=false
            shift
            ;;
        --no-archive)
            ARCHIVE=false
            shift
            ;;
        --testbed)
            TESTBED_FILE="$2"
            shift 2
            ;;
        --help|-h)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Banner
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  EVPN Cleanup Execution Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Validate testbed file
if [ ! -f "$TESTBED_FILE" ]; then
    print_error "Testbed file not found: $TESTBED_FILE"
    exit 1
fi
print_info "Testbed file: $TESTBED_FILE"

# Validate cleanup configs directory
if [ ! -d "$CLEANUP_DIR" ]; then
    print_error "Cleanup configs directory not found: $CLEANUP_DIR"
    print_info "Run generate_evpn_cleanup.py first to create cleanup configs"
    exit 1
fi
print_info "Cleanup configs: $CLEANUP_DIR"

# Count cleanup configs
CLEANUP_COUNT=$(find "$CLEANUP_DIR" -name "*_evpn_cleanup.cfg" | wc -l | tr -d ' ')
print_info "Found $CLEANUP_COUNT cleanup configuration files"

# Create log directory
mkdir -p "$LOG_DIR"

# Show configuration
echo ""
echo -e "${YELLOW}Configuration:${NC}"
if [ -n "$DEVICES" ]; then
    echo "  Target devices: $DEVICES"
else
    echo "  Target devices: All devices with cleanup configs"
fi

if [ "$DRY_RUN" = true ]; then
    echo -e "  Mode: ${YELLOW}DRY RUN (no changes will be applied)${NC}"
else
    echo -e "  Mode: ${RED}LIVE (cleanup will be applied)${NC}"
fi

echo "  Interactive: $INTERACTIVE"
echo "  Archive results: $ARCHIVE"
echo ""

# Show what will be removed/preserved
echo -e "${YELLOW}What will be removed:${NC}"
echo "  ✗ BGP EVPN address-families"
echo "  ✗ NVE interfaces"
echo "  ✗ L2VPN EVPN instances"
echo "  ✗ EVPN VRFs and VLANs"
echo "  ✗ SVI interfaces"
echo ""
echo -e "${GREEN}What will be preserved:${NC}"
echo "  ✓ ISIS routing protocol"
echo "  ✓ OSPF routing protocol"
echo "  ✓ Physical interfaces"
echo "  ✓ Management VRF"
echo "  ✓ Basic device configuration"
echo ""

# Interactive confirmation
if [ "$INTERACTIVE" = true ] && [ "$DRY_RUN" = false ]; then
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}WARNING: This will modify device configs!${NC}"
    echo -e "${RED}========================================${NC}"
    echo ""
    read -p "Do you want to proceed with EVPN cleanup? (yes/no): " CONFIRM
    
    if [ "$CONFIRM" != "yes" ]; then
        print_warning "Cleanup cancelled by user"
        exit 0
    fi
    echo ""
fi

# Build PyATS command
PYATS_CMD="pyats run job apply_evpn_cleanup_job.py --testbed-file $TESTBED_FILE"

if [ -n "$DEVICES" ]; then
    PYATS_CMD="$PYATS_CMD --devices $DEVICES"
fi

if [ "$DRY_RUN" = true ]; then
    PYATS_CMD="$PYATS_CMD --dry-run"
fi

# Set log file
LOG_FILE="${LOG_DIR}/cleanup_${TIMESTAMP}.log"

# Run PyATS job
print_info "Starting EVPN cleanup job..."
print_info "Command: $PYATS_CMD"
print_info "Log file: $LOG_FILE"
echo ""

# Execute PyATS job
if $PYATS_CMD 2>&1 | tee "$LOG_FILE"; then
    EXIT_CODE=0
else
    EXIT_CODE=$?
fi

echo ""

# Check results
if [ $EXIT_CODE -eq 0 ]; then
    print_success "EVPN cleanup job completed successfully!"
    
    # Find the PyATS results directory
    RESULTS_DIR=$(find . -maxdepth 1 -type d -name "archive_*" 2>/dev/null | sort -r | head -n 1)
    
    if [ -n "$RESULTS_DIR" ]; then
        print_info "PyATS results: $RESULTS_DIR"
        
        # Archive results if requested
        if [ "$ARCHIVE" = true ]; then
            ARCHIVE_NAME="cleanup_results_${TIMESTAMP}.tar.gz"
            print_info "Archiving results to: $ARCHIVE_NAME"
            tar -czf "$ARCHIVE_NAME" "$RESULTS_DIR" "$LOG_FILE" 2>/dev/null || true
            
            if [ -f "$ARCHIVE_NAME" ]; then
                print_success "Results archived: $ARCHIVE_NAME"
            fi
        fi
    fi
    
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}Next Steps:${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo "1. Review the cleanup report in PyATS results"
    echo "2. Verify EVPN components are removed:"
    echo "   - show l2vpn evpn"
    echo "   - show interface nve1"
    echo "   - show vrf"
    echo "3. Verify underlay routing is intact:"
    echo "   - show isis neighbors"
    echo "   - show ip route"
    echo "4. Check device logs for any errors"
    echo ""
    
else
    print_error "EVPN cleanup job failed with exit code: $EXIT_CODE"
    print_info "Check log file for details: $LOG_FILE"
    echo ""
    exit $EXIT_CODE
fi

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Cleanup Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
echo "Log file: $LOG_FILE"

if [ -n "$RESULTS_DIR" ]; then
    echo "Results: $RESULTS_DIR"
fi

if [ "$DRY_RUN" = true ]; then
    echo -e "Mode: ${YELLOW}DRY RUN (no changes applied)${NC}"
else
    echo -e "Mode: ${GREEN}LIVE (cleanup applied)${NC}"
fi

echo -e "${BLUE}========================================${NC}"
echo ""
