#!/bin/bash
# Pre-push hook: run tests and abort if they fail

cd "$(dirname "$0")/.."
py -m pytest -q
if [ $? -ne 0 ]; then
  echo "Tests failed. Push aborted."
  exit 1
fi 