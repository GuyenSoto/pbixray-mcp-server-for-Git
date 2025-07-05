# Testing the PBIXRay MCP Server

This document provides guidance on how to test the PBIXRay MCP Server using the MCP Inspector and other testing methods.

## Using MCP Inspector

The MCP Inspector is a powerful tool for testing and debugging MCP servers. It provides a web-based interface to interact with your server, call tools, view responses, and debug issues.

### Prerequisites

- Node.js and npm installed on your system
- The MCP Inspector package (installed automatically through npx)
- A sample PBIX file for testing (available in the `demo/` directory)

### Starting the Inspector

To test your PBIXRay server with the MCP Inspector:

```bash
# Navigate to your project directory
cd path/to/pbixray-mcp

# Run the server with MCP Inspector
npx -y @modelcontextprotocol/inspector python src/pbixray_server.py
```

This command will:
1. Download and run the MCP Inspector if it's not already installed
2. Start your PBIXRay server 
3. Open a web interface at http://localhost:5173

### Using the Inspector Interface

Once the Inspector is running, you'll see a web interface with several sections:

1. **Connection Information**: Shows the server name, version, and connection status
2. **Tools**: Lists all tools exposed by your server
3. **Request/Response Panel**: Shows tool calls and their responses

#### Testing Tools

To test a tool in the PBIXRay server:

1. In the tools section, find the tool you want to test (e.g., `load_pbix_file`)
2. Click on the tool to view its parameters
3. Fill in the required parameters
   - For `load_pbix_file`, enter the path to a sample PBIX file (e.g., `demo/AdventureWorks Sales.pbix`)
4. Click "Execute" to call the tool
5. View the response in the response panel

#### Testing Workflow

A typical testing workflow might look like:

1. Call `load_pbix_file` to load a PBIX file for analysis
2. Call `get_model_summary` to see a high-level overview of the model
3. Call `get_tables` to list all tables in the model
4. Call `get_dax_measures` to view all DAX measures
5. Call `get_table_contents` with a specific table name to view its data

### Troubleshooting Inspector Issues

Common issues and their solutions:

1. **Connection Errors**
   - Make sure your PBIXRay server doesn't have syntax errors
   - Check if the path to your server script is correct
   - Ensure all dependencies are installed

2. **Path Issues with PBIX Files**
   - Use absolute paths for PBIX files
   - Verify the file exists at the specified location
   - Make sure file permissions allow reading the file

3. **Inspector Won't Start**
   - Check Node.js and npm versions (Node.js 14+ recommended)
   - Try clearing npm cache: `npm cache clean --force`
   - Check for port conflicts on 5173 or 3000

### Stopping the Inspector

To stop the Inspector:
- Press `Ctrl+C` in the terminal where it's running
- Close the browser window

## Automated Testing

The project includes automated tests in the `tests/` directory. To run all tests:

```bash
# Activate your virtual environment
source venv/bin/activate

# Run all tests
pytest
```

### Testing with a Custom PBIX File

By default, the tests use the demo PBIX file included in the repository (`demo/AdventureWorks Sales.pbix`). 
You can specify a custom PBIX file to use in the tests with the `--pbix-file` option:

```bash
# Test with a specific PBIX file
pytest tests/test_server.py --pbix-file=/path/to/your/custom.pbix

# Test just the large file handling with a custom PBIX
pytest tests/test_server.py::test_large_file_handling --pbix-file=/path/to/large.pbix
```

This is useful for testing with:
- Large PBIX files to verify timeout handling
- Files with complex structures or relationships
- Files that have caused issues in the past

### Running Specific Tests

To run specific test files or functions:

```bash
# Run a specific test file
pytest tests/test_server.py

# Run a specific test function
pytest tests/test_server.py::test_load_pbix_file
```

All test functions that use real PBIX files will automatically use the file specified with `--pbix-file` if provided.

## Interactive Demo

For a more guided testing experience, try the interactive demo:

```bash
python examples/demo.py
```

This will connect to the server and provide a menu-driven interface to test various features.

## Testing with Claude for Desktop

Once your server is working correctly with the MCP Inspector, you can configure it to work with Claude for Desktop:

1. Edit your Claude for Desktop configuration file:
   - On macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - On Windows: `%APPDATA%\Claude\claude_desktop_config.json`

2. Add your server configuration:
   ```json
   {
     "mcpServers": {
       "pbixray": {
         "command": "python",
         "args": ["/path/to/src/pbixray_server.py"]
       }
     }
   }
   ```

3. Restart Claude for Desktop and look for the tools icon to verify connection.

## Logging and Debugging

For more detailed logging during testing:

```bash
# Enable verbose logging
PYTHONVERBOSE=1 python src/pbixray_server.py
```

This will show more detailed logs about tool calls, errors, and server operations.

## Test Coverage

The automated tests cover:

1. **Basic Functionality**
   - Loading PBIX files
   - Retrieving tables and metadata
   - Getting model summaries and statistics

2. **Large File Handling**
   - Tests specifically for large file loading
   - Progress reporting during long operations
   - Thread pool processing for CPU-intensive operations

3. **Asynchronous Operations**
   - Testing of async functions
   - Proper cancellation of background tasks
   - Resource cleanup

4. **Error Handling**
   - Testing for proper error reporting
   - Handling of missing files or invalid paths
   - Recovery from failures

The tests use both the actual demo PBIX file and mock objects, ensuring both real-world usage and edge cases are covered.

## Common Testing Issues

1. **Missing Libraries**
   - Ensure `pbixray`, `numpy`, and `mcp` packages are installed
   - Install: `pip install -r requirements.txt`
   - For testing, also install `pytest` and `pytest-asyncio`

2. **File Path Issues**
   - Always use absolute paths when testing with PBIX files
   - Check file permissions if you get access denied errors
   - Use the `--pbix-file` option for custom PBIX files

3. **Data Format Issues**
   - If you see JSON serialization errors, check the `NumpyEncoder` in the server code
   - Large datasets may need limiting with pagination or sampling

4. **Timeouts with Large Files**
   - If you're still experiencing timeouts, the server includes a fix for this
   - Use the `test_large_file_handling` test to verify timeout handling

## Next Steps

After successful testing, you may want to:

1. Integrate with your preferred MCP client
2. Add additional tools or features to the server
3. Contribute improvements to the project (see CONTRIBUTING.md)

For feature requests or bug reports discovered during testing, please open an issue on the project repository.