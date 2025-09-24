#!/bin/bash
cd /home/kavia/workspace/code-generation/uv-ready-python-scaffold-36105-36114/backend_server
source venv/bin/activate
flake8 .
LINT_EXIT_CODE=$?
if [ $LINT_EXIT_CODE -ne 0 ]; then
  exit 1
fi

