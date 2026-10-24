#!/bin/bash
set -e

echo "=== Harness Initialization ==="

PYTHON_BIN="python3"
if [ -f "./venv/bin/python" ]; then
  PYTHON_BIN="./venv/bin/python"
fi

echo "=== Running Tests ==="
$PYTHON_BIN -m pytest || [ $? -eq 5 ]

echo "=== Checking Syntax ==="
$PYTHON_BIN -m compileall -q -x '(^|/)(\.?venv|env|node_modules|build|dist|__pycache__)(/|$)' .

echo "=== Verification Complete ==="
echo ""
echo "Next steps:"
echo "1. Read feature_list.json to see current feature state"
echo "2. Pick ONE unfinished feature to work on"
echo "3. Implement only that feature"
echo "4. Re-run verification before claiming done"
