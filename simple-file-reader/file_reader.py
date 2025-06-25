#!/usr/bin/env python3

import asyncio
import os
import sys
from typing import Any, Sequence

import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio

# Create server instance
app = Server("file-reader")

@app.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools."""
    return [
        types.Tool(
            name="read_file",
            description="Read a text file from your local machine",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string", 
                        "description": "Path to the text file you want to read"
                    }
                },
                "required": ["file_path"]
            }
        ),
        types.Tool(
            name="list_files",
            description="List files in a directory",
            inputSchema={
                "type": "object",
                "properties": {
                    "directory_path": {
                        "type": "string", 
                        "description": "Path to the directory to list (defaults to home directory)"
                    }
                },
                "required": []
            }
        )
    ]

@app.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool calls."""
    
    if name == "read_file":
        file_path = arguments["file_path"]
        
        # Expand ~ to home directory
        file_path = os.path.expanduser(file_path)
        
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                return [types.TextContent(
                    type="text", 
                    text=f"Error: File '{file_path}' does not exist"
                )]
            
            # Check if it's actually a file
            if not os.path.isfile(file_path):
                return [types.TextContent(
                    type="text", 
                    text=f"Error: '{file_path}' is not a file"
                )]
            
            # Read the file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return [types.TextContent(
                type="text", 
                text=f"Content of '{file_path}':\n\n{content}"
            )]
            
        except PermissionError:
            return [types.TextContent(
                type="text", 
                text=f"Error: Permission denied reading '{file_path}'"
            )]
        except UnicodeDecodeError:
            return [types.TextContent(
                type="text", 
                text=f"Error: Cannot read '{file_path}' - file appears to be binary or not UTF-8 encoded"
            )]
        except Exception as e:
            return [types.TextContent(
                type="text", 
                text=f"Error reading file: {str(e)}"
            )]
    
    elif name == "list_files":
        directory_path = arguments.get("directory_path", "~")
        
        # Expand ~ to home directory
        directory_path = os.path.expanduser(directory_path)
        
        try:
            # Check if directory exists
            if not os.path.exists(directory_path):
                return [types.TextContent(
                    type="text", 
                    text=f"Error: Directory '{directory_path}' does not exist"
                )]
            
            # Check if it's actually a directory
            if not os.path.isdir(directory_path):
                return [types.TextContent(
                    type="text", 
                    text=f"Error: '{directory_path}' is not a directory"
                )]
            
            # List files and directories
            items = []
            for item in sorted(os.listdir(directory_path)):
                item_path = os.path.join(directory_path, item)
                if os.path.isdir(item_path):
                    items.append(f"📁 {item}/")
                else:
                    items.append(f"📄 {item}")
            
            files_list = "\n".join(items)
            return [types.TextContent(
                type="text", 
                text=f"Contents of '{directory_path}':\n\n{files_list}"
            )]
            
        except PermissionError:
            return [types.TextContent(
                type="text", 
                text=f"Error: Permission denied accessing '{directory_path}'"
            )]
        except Exception as e:
            return [types.TextContent(
                type="text", 
                text=f"Error listing directory: {str(e)}"
            )]
    
    else:
        raise ValueError(f"Unknown tool: {name}")

async def main():
    # Run the server using stdin/stdout streams
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())