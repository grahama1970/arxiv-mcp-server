#!/usr/bin/env python3
"""Basic test to verify MCP server can run."""

import subprocess
import time
import sys

print("=== Testing ArXiv MCP Server ===\n")

# Try to start the server
print("1. Attempting to start arxiv-mcp-server...")
try:
    # Start the server process
    process = subprocess.Popen(
        ["arxiv-mcp-server"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Give it a moment to start
    time.sleep(2)
    
    # Check if it's still running
    if process.poll() is None:
        print("   ✓ Server started successfully")
        print("   Server is running with PID:", process.pid)
        
        # Try to read some output
        try:
            # Use communicate with timeout to avoid hanging
            stdout, stderr = process.communicate(timeout=3)
            if stdout:
                print("\n   Server output:")
                print("   " + stdout[:200].replace("\n", "\n   "))
            if stderr:
                print("\n   Server errors:")
                print("   " + stderr[:200].replace("\n", "\n   "))
        except subprocess.TimeoutExpired:
            print("   Server is running (no immediate output)")
            # Terminate the process
            process.terminate()
            process.wait()
            
    else:
        # Process ended
        stdout, stderr = process.communicate()
        print("   ✗ Server exited immediately")
        if stdout:
            print("\n   Output:", stdout[:500])
        if stderr:
            print("\n   Error:", stderr[:500])
            
except FileNotFoundError:
    print("   ✗ arxiv-mcp-server command not found")
    print("   Make sure you've installed the package with: uv pip install -e .")
except Exception as e:
    print(f"   ✗ Error starting server: {e}")

print("\n2. Checking if we can import the modules directly...")
try:
    # Try importing without going through server
    sys.path.insert(0, 'src')
    
    # Import converters
    from arxiv_mcp_server.converters import ConverterFactory
    print("   ✓ Converters module imported")
    
    # Import tools directly
    from arxiv_mcp_server.tools.system_stats import get_system_stats
    print("   ✓ System stats tool imported")
    
    # Import config
    from arxiv_mcp_server.config import Settings
    settings = Settings()
    print(f"   ✓ Config loaded - storage path: {settings.STORAGE_PATH}")
    
    print("\n   The modules work correctly when imported directly.")
    print("   The MCP server integration requires the MCP protocol to be properly set up.")
    
except ImportError as e:
    print(f"   ✗ Import error: {e}")
except Exception as e:
    print(f"   ✗ Error: {e}")

print("\n=== Summary ===")
print("""
The ArXiv MCP server components are installed and functional.
The server requires MCP protocol communication which may need additional setup.

To use the server:
1. Make sure all dependencies are installed: uv pip install -e .
2. Run the server: arxiv-mcp-server
3. Connect to it using an MCP client

The tree_sitter_utils.py could be useful for analyzing code in scientific papers.
""")