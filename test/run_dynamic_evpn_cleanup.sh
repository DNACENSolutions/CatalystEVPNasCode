#!/bin/bash
#
# Dynamic EVPN Cleanup Execution Script
# Intelligently removes EVPN/VXLAN without static config files
# Handles partial cleanups gracefully
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TESTBED_FILE="${SCRIPT_DIR}/evpn_testbed.yaml"

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

Dynamic EVPN Cleanup Script - Intelligently removes EVPN/VXLAN components

OPTIONS:
    -d, --devices DEVICES    Comma-separated list of device names (default: all)
    -t, --testbed FILE       Path to testbed file (default: evpn_testbed.yaml)
    -b, --remove-bgp         Remove BGP completely (default: preserve BGP, remove EVPN only)
    -h, --help              Show this help message

EXAMPLES:
    # Clean all devices (preserve BGP)
    $0

    # Clean specific devices
    $0 --devices TB16-Fusion,TB16-Spine

    # Clean all devices and remove BGP completely
    $0 --remove-bgp

    # Clean specific device with BGP removal
    $0 -d TB16-SJ-Leaf-1 -b

FEATURES:
    ✓ Intelligent detection of EVPN components
    ✓ Handles partial cleanups gracefully
    ✓ Continues on errors (items already removed)
    ✓ No static config files needed
    ✓ Preserves ISIS/OSPF underlay
    ✓ Preserves management VRF

EOF
    exit 1
}

# Parse command line arguments
DEVICES=""
REMOVE_BGP=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--devices)
            DEVICES="$2"
            shift 2
            ;;
        -t|--testbed)
            TESTBED_FILE="$2"
            shift 2
            ;;
        -b|--remove-bgp)
            REMOVE_BGP="--remove-bgp"
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

# Verify testbed file exists
if [ ! -f "$TESTBED_FILE" ]; then
    print_error "Testbed file not found: $TESTBED_FILE"
    exit 1
fi

# Display banner
echo ""
echo "=========================================="
echo "  Dynamic EVPN Cleanup"
echo "=========================================="
echo ""
print_info "Testbed: $TESTBED_FILE"

if [ -n "$DEVICES" ]; then
    print_info "Target Devices: $DEVICES"
else
    print_info "Target Devices: ALL (except BASE-DEVICE)"
fi

if [ -n "$REMOVE_BGP" ]; then
    print_warning "BGP will be COMPLETELY REMOVED"
else
    print_info "BGP will be preserved (only EVPN removed)"
fi

echo ""

# Confirmation prompt
read -p "Do you want to proceed? (yes/no): " -r
echo
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    print_warning "Cleanup cancelled by user"
    exit 0
fi

# Build pyats command
PYATS_CMD="pyats run job apply_dynamic_evpn_cleanup_job.py --testbed-file $TESTBED_FILE"

if [ -n "$DEVICES" ]; then
    PYATS_CMD="$PYATS_CMD --devices $DEVICES"
fi

if [ -n "$REMOVE_BGP" ]; then
    PYATS_CMD="$PYATS_CMD $REMOVE_BGP"
fi

# Execute cleanup
print_info "Starting dynamic EVPN cleanup..."
echo ""

cd "$SCRIPT_DIR" || exit 1

eval "$PYATS_CMD"

EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    print_success "Dynamic EVPN cleanup completed successfully!"
else
    print_error "Dynamic EVPN cleanup failed with exit code: $EXIT_CODE"
fi

echo ""
print_info "Check the PyATS logs for detailed results"
echo ""

exit $EXIT_CODE
