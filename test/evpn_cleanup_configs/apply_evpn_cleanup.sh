#!/bin/bash
#
# BGP EVPN Cleanup Master Script
# Generated: 2026-02-09 13:41:02
#
# This script applies EVPN cleanup configurations to all devices
#

set -e

# Color codes for output
GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[1;33m"
NC="\033[0m" # No Color

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CLEANUP_DIR="${SCRIPT_DIR}/evpn_cleanup_configs"
LOG_DIR="${SCRIPT_DIR}/cleanup_logs"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p "${LOG_DIR}"

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}BGP EVPN Cleanup Script${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

# Device list
DEVICES=(
  "TB16-Fusion"
  "TB16-SJ-BORDER-1"
  "TB16-SJ-BORDER-2"
  "TB16-SJ-Border-3"
  "TB16-SJ-Leaf-1"
  "TB16-SJ-Leaf-2"
  "TB16-SJ-Leaf-3"
  "TB16-Spine"
)

echo -e "${YELLOW}Devices to clean:${NC}"
for device in "${DEVICES[@]}"; do
  echo "  - $device"
done
echo ""

read -p "Do you want to proceed with cleanup? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
  echo -e "${RED}Cleanup cancelled.${NC}"
  exit 1
fi
echo ""

# Apply cleanup to each device
for device in "${DEVICES[@]}"; do
  echo -e "${YELLOW}Processing $device...${NC}"
  
  CLEANUP_FILE="${CLEANUP_DIR}/${device}_evpn_cleanup.cfg"
  LOG_FILE="${LOG_DIR}/${device}_cleanup_${TIMESTAMP}.log"
  
  if [ ! -f "$CLEANUP_FILE" ]; then
    echo -e "${RED}  ✗ Cleanup file not found: $CLEANUP_FILE${NC}"
    continue
  fi
  
  # TODO: Add your device connection and config application logic here
  # Example using expect or PyATS:
  # pyats run job apply_config_job.py --testbed-file evpn_testbed.yaml \
  #   --device "$device" --config-file "$CLEANUP_FILE" --log-file "$LOG_FILE"
  
  echo -e "${GREEN}  ✓ Cleanup config ready: $CLEANUP_FILE${NC}"
  echo "    Review and apply manually or integrate with automation"
done

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Cleanup configs generated successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Next steps:"
echo "1. Review cleanup configs in: ${CLEANUP_DIR}"
echo "2. Apply configs manually or via automation"
echo "3. Verify EVPN components are removed"
echo "4. Check that ISIS/OSPF remain intact"
