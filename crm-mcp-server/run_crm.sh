#!/bin/bash
cd <replace_with_full_path>/simple_mcp/crm-mcp-server/
source venv/bin/activate
# conda activate mcp_exp
exec python crm_server.py "$@"