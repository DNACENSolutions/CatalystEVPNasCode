#!/bin/bash
#
# OSPF Underlay Application Script
# Applies OSPF configurations to devices
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

OSPF Underlay Application Script - Applies OSPF routing to devices

OPTIONS:
    -d, --devices DEVICES    Comma-separated list of device names (default: all)
    -t, --testbed FILE       Path to testbed file (default: evpn_testbed.yaml)
    -n, --dry-run           Dry run mode (no changes applied)
    -h, --help              Show this help message

EXAMPLES:
    # Apply OSPF to all devices
    $0

    # Apply to specific devices
    $0 --devices TB16-Spine,TB16-SJ-Leaf-1

    # Dry run to see what would be applied
    $0 --dry-run

    # Specific devices with dry run
    $0 -d TB16-Fusion -n

FEATURES:
    ✓ Preserves existing IP addresses
    ✓ Configures OSPF process 1 with area 0
    ✓ Uses Loopback0 IP as router-id
    ✓ Enables OSPF on all underlay interfaces
    ✓ Backs up configs before applying
    ✓ Verifies OSPF neighbors after application

EOF
    exit 1
}

# Parse command line arguments
DEVICES=""
DRY_RUN=""

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
        -n|--dry-run)
            DRY_RUN="--dry-run"
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

# Verify OSPF configs exist
if [ ! -d "$SCRIPT_DIR/ospf_underlay_configs" ]; then
    print_error "OSPF config directory not found: $SCRIPT_DIR/ospf_underlay_configs"
    print_info "Run 'python3 generate_ospf_underlay.py' first to generate configs"
    exit 1
fi

# Display banner
echo ""
echo "=========================================="
echo "  OSPF Underlay Application"
echo "=========================================="
echo ""
print_info "Testbed: $TESTBED_FILE"

if [ -n "$DEVICES" ]; then
    print_info "Target Devices: $DEVICES"
else
    print_info "Target Devices: ALL (except BASE-DEVICE)"
fi

if [ -n "$DRY_RUN" ]; then
    print_warning "DRY RUN MODE - No changes will be applied"
fi

echo ""

# Confirmation prompt (skip for dry-run)
if [ -z "$DRY_RUN" ]; then
    read -p "Do you want to proceed? (yes/no): " -r
    echo
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        print_warning "OSPF application cancelled by user"
        exit 0
    fi
fi

# Build pyats command
PYATS_CMD="pyats run job apply_ospf_underlay_job.py --testbed-file $TESTBED_FILE"

if [ -n "$DEVICES" ]; then
    PYATS_CMD="$PYATS_CMD --devices $DEVICES"
fi

if [ -n "$DRY_RUN" ]; then
    PYATS_CMD="$PYATS_CMD $DRY_RUN"
fi

# Execute OSPF application
print_info "Starting OSPF underlay application..."
echo ""

cd "$SCRIPT_DIR" || exit 1

eval "$PYATS_CMD"

EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    print_success "OSPF underlay application completed successfully!"
else
    print_error "OSPF underlay application failed with exit code: $EXIT_CODE"
fi

echo ""
print_info "Check the PyATS logs for detailed results"
echo ""

exit $EXIT_CODE
