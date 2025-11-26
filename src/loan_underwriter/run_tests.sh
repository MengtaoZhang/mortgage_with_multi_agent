#!/bin/bash
# Script to run tests with proper Python path setup

cd "$(dirname "$0")"

export PYTHONPATH="$(pwd):$(pwd)/..:$PYTHONPATH"

echo "Running tests with PYTHONPATH=$(pwd):$(pwd)/.."
echo ""

python -m pytest test/test_scenario_1_assertions.py -v -s "$@"
