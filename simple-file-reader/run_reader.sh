#!/bin/bash
cd <replace_with_full_path>/simple_mcp/simple-file-reader/
source venv/bin/activate
# conda activate mcp_exp
exec python file_reader.py "$@"