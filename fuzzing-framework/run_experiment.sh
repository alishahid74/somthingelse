#!/bin/bash

# Quick Start Script for Fuzzing Framework
# Usage: ./run_experiment.sh <target_binary> [duration_in_seconds]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  AFL++ + PPO Fuzzing Framework${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check arguments
if [ $# -lt 1 ]; then
    echo -e "${RED}Error: Missing target binary${NC}"
    echo "Usage: $0 <target_binary> [duration_in_seconds]"
    echo ""
    echo "Examples:"
    echo "  $0 /path/to/binary 3600          # Run for 1 hour"
    echo "  $0 /path/to/binary 7200          # Run for 2 hours"
    exit 1
fi

TARGET_BINARY="$1"
DURATION="${2:-3600}"  # Default 1 hour

# Validate target binary
if [ ! -f "$TARGET_BINARY" ]; then
    echo -e "${RED}Error: Target binary not found: $TARGET_BINARY${NC}"
    exit 1
fi

if [ ! -x "$TARGET_BINARY" ]; then
    echo -e "${YELLOW}Warning: Target binary is not executable${NC}"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check AFL++ installation
if ! command -v afl-fuzz &> /dev/null; then
    echo -e "${RED}Error: AFL++ not found. Please install AFL++ first.${NC}"
    echo "Visit: https://github.com/AFLplusplus/AFLplusplus"
    exit 1
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python3 not found${NC}"
    exit 1
fi

# Setup virtual environment if needed
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

echo -e "${GREEN}Activating virtual environment...${NC}"
source venv/bin/activate

# Install requirements
if [ ! -f ".requirements_installed" ]; then
    echo -e "${YELLOW}Installing Python dependencies...${NC}"
    pip install -q -r requirements.txt
    touch .requirements_installed
    echo -e "${GREEN}Dependencies installed${NC}"
fi

# Create input directory if it doesn't exist
if [ ! -d "data/inputs" ]; then
    echo -e "${YELLOW}Creating input directory with seed files...${NC}"
    mkdir -p data/inputs
    echo "test" > data/inputs/seed1.txt
    echo "hello" > data/inputs/seed2.txt
    echo "fuzzing" > data/inputs/seed3.txt
    echo -e "${GREEN}Created seed inputs${NC}"
fi

# Display configuration
echo ""
echo -e "${BLUE}Experiment Configuration:${NC}"
echo -e "  Target Binary: ${GREEN}$TARGET_BINARY${NC}"
echo -e "  Duration:      ${GREEN}$DURATION seconds ($(echo "scale=2; $DURATION/3600" | bc) hours)${NC}"
echo -e "  Mode:          ${GREEN}Comparison (Baseline + PPO)${NC}"
echo -e "  Total Time:    ${GREEN}$(echo "scale=2; $DURATION*2/3600" | bc) hours${NC}"
echo ""

# Confirm
read -p "Start experiment? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
fi

echo ""
echo -e "${GREEN}Starting experiments...${NC}"
echo ""

# Run experiments
cd src
python3 experiment_runner.py "$TARGET_BINARY" \
    --mode comparison \
    --duration "$DURATION" \
    --afl-config ../config/afl_config.yaml \
    --ppo-config ../config/ppo_config.yaml

EXPERIMENT_STATUS=$?

if [ $EXPERIMENT_STATUS -eq 0 ]; then
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  Experiments Completed Successfully!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""

    # Generate visualizations
    echo -e "${BLUE}Generating comparison graphs...${NC}"
    cd ../visualization
    python3 graph_generator.py \
        --metrics-dir ../data/results/comparison \
        --output-dir ../graphs

    echo ""
    echo -e "${GREEN}Results Summary:${NC}"
    echo -e "  Metrics:  ${BLUE}data/results/comparison/${NC}"
    echo -e "  Graphs:   ${BLUE}graphs/${NC}"
    echo -e "  Reports:  ${BLUE}reports/${NC}"
    echo ""

    echo -e "${YELLOW}Next Steps:${NC}"
    echo "  1. View graphs: cd graphs && ls *.png"
    echo "  2. Read report: cat ../data/results/comparison/paper_results.txt"
    echo "  3. Generate detailed report: cd ../visualization && python report_generator.py"
    echo ""

else
    echo ""
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}  Experiment Failed${NC}"
    echo -e "${RED}========================================${NC}"
    echo ""
    echo "Check the output above for errors."
    exit 1
fi
