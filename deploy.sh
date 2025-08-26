#!/bin/bash

# EVPN Fabric Deployment Execution Script
# This script provides easy execution options for the EVPN deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Function to print colored output
print_status() {
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

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if ansible is installed
    if ! command -v ansible &> /dev/null; then
        print_error "Ansible is not installed. Please install ansible first."
        exit 1
    fi
    
    # Check if required files exist
    if [ ! -f "$SCRIPT_DIR/evpn_deployment.yml" ]; then
        print_error "Master playbook evpn_deployment.yml not found!"
        exit 1
    fi
    
    if [ ! -f "$SCRIPT_DIR/data/sites.yml" ]; then
        print_error "Site configuration file data/sites.yml not found!"
        exit 1
    fi
    
    # Check environment variables
    if [ -z "$CATALYST_CENTER_HOSTNAME" ]; then
        print_warning "CATALYST_CENTER_HOSTNAME environment variable not set"
    fi
    
    print_success "Prerequisites check completed"
}

# Function to validate playbook syntax
validate_syntax() {
    print_status "Validating playbook syntax..."
    if ansible-playbook "$SCRIPT_DIR/evpn_deployment.yml" --syntax-check; then
        print_success "Playbook syntax is valid"
    else
        print_error "Playbook syntax validation failed"
        exit 1
    fi
}

# Function to display help
show_help() {
    echo "EVPN Fabric Deployment Script"
    echo ""
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  deploy              Deploy complete EVPN fabric (all phases)"
    echo "  phase1              Execute Phase 1: ISE Integration"
    echo "  phase2              Execute Phase 2: Site Hierarchy Design"
    echo "  phase3              Execute Phase 3: Global Credentials"
    echo "  phase4              Execute Phase 4: Network Settings"
    echo "  phase5              Execute Phase 5: IP Pools"
    echo "  phase6              Execute Phase 6: Device Discovery"
    echo "  phase7              Execute Phase 7: Site Assignment"
    echo "  phase8              Execute Phase 8: LAN Automation"
    echo "  phase9              Execute Phase 9: Device Provisioning"
    echo "  phase10             Execute Phase 10: Template Creation"
    echo "  phase11             Execute Phase 11: Template Deployment"
    echo "  phase12             Execute Phase 12: Validation"
    echo "  validate            Run validation only"
    echo "  check               Check prerequisites and syntax"
    echo "  help                Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  CATALYST_CENTER_HOSTNAME  - Catalyst Center hostname/IP"
    echo "  CATALYST_CENTER_USERNAME  - Catalyst Center username"
    echo "  CATALYST_CENTER_PASSWORD  - Catalyst Center password"
    echo ""
    echo "Examples:"
    echo "  $0 deploy           # Deploy complete fabric"
    echo "  $0 phase1           # Execute only ISE integration"
    echo "  $0 validate         # Run validation checks"
}

# Function to execute deployment phases
execute_phase() {
    local phase=$1
    local description=$2
    local tags=$3
    
    print_status "Starting $description"
    echo "======================================================================"
    
    if ansible-playbook "$SCRIPT_DIR/evpn_deployment.yml" --tags "$tags" -v; then
        print_success "$description completed successfully"
    else
        print_error "$description failed"
        exit 1
    fi
    
    echo "======================================================================"
    echo ""
}

# Main execution logic
case "$1" in
    "deploy")
        check_prerequisites
        validate_syntax
        print_status "Starting complete EVPN fabric deployment..."
        ansible-playbook "$SCRIPT_DIR/evpn_deployment.yml" -v
        print_success "EVPN fabric deployment completed successfully!"
        ;;
    "phase1")
        check_prerequisites
        validate_syntax
        execute_phase "1" "Phase 1: ISE Integration" "phase1,ise"
        ;;
    "phase2")
        check_prerequisites
        validate_syntax
        execute_phase "2" "Phase 2: Site Hierarchy Design" "phase2,sites"
        ;;
    "phase3")
        check_prerequisites
        validate_syntax
        execute_phase "3" "Phase 3: Global Credentials" "phase3,credentials"
        ;;
    "phase4")
        check_prerequisites
        validate_syntax
        execute_phase "4" "Phase 4: Network Settings" "phase4,network"
        ;;
    "phase5")
        check_prerequisites
        validate_syntax
        execute_phase "5" "Phase 5: IP Pools" "phase5,pools"
        ;;
    "phase6")
        check_prerequisites
        validate_syntax
        execute_phase "6" "Phase 6: Device Discovery" "phase6,discovery"
        ;;
    "phase7")
        check_prerequisites
        validate_syntax
        execute_phase "7" "Phase 7: Site Assignment" "phase7,assignment"
        ;;
    "phase8")
        check_prerequisites
        validate_syntax
        execute_phase "8" "Phase 8: LAN Automation" "phase8,automation"
        ;;
    "phase9")
        check_prerequisites
        validate_syntax
        execute_phase "9" "Phase 9: Device Provisioning" "phase9,provision"
        ;;
    "phase10")
        check_prerequisites
        validate_syntax
        execute_phase "10" "Phase 10: Template Creation" "phase10,templates"
        ;;
    "phase11")
        check_prerequisites
        validate_syntax
        execute_phase "11" "Phase 11: Template Deployment" "phase11,deploy"
        ;;
    "phase12")
        check_prerequisites
        validate_syntax
        execute_phase "12" "Phase 12: Validation" "phase12,validate"
        ;;
    "validate")
        check_prerequisites
        validate_syntax
        execute_phase "validation" "EVPN Fabric Validation" "phase12,validate"
        ;;
    "check")
        check_prerequisites
        validate_syntax
        print_success "All checks passed!"
        ;;
    "help"|"--help"|"-h")
        show_help
        ;;
    "")
        print_error "No option specified"
        show_help
        exit 1
        ;;
    *)
        print_error "Invalid option: $1"
        show_help
        exit 1
        ;;
esac
