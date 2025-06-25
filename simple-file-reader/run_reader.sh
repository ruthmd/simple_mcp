#!/bin/bash
cd <replace_with_full_path>/simple_mcp/simple-file-reader/

# venv
# source venv/bin/activate

# miniconda
# /home/username/miniconda3/etc/profile.d/conda.sh

# anaconda
source <anaconda_installation_path>/anaconda3/etc/profile.d/conda.sh
conda activate mcp_exp
exec python file_reader.py "$@"