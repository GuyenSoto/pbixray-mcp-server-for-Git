#!/bin/bash
# Script to run PBIXRay MCP Server with automatic loading of a PBIX file
cd "$(dirname "$0")"
source venv/bin/activate
python src/pbixray_server.py --load-file "informe_mercado.pbix" "$@"
