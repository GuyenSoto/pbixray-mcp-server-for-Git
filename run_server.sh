#!/bin/bash
# Script to run PBIXRay MCP Server with proper environment
cd "$(dirname "$0")"
source venv/bin/activate
python src/pbixray_server.py "$@"
