#!/bin/bash
cd <replace_with_full_path>/github_repos/simple_mcp/crm-mcp-server/

# venv
# source venv/bin/activate

# miniconda
# /home/username/miniconda3/etc/profile.d/conda.sh

# anaconda
source <anaconda_installation_path>/anaconda3/etc/profile.d/conda.sh
conda activate mcp_exp
exec python crm_server.py "$@"