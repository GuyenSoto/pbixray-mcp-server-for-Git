# PBIXRay MCP Server

[![MseeP.ai Security Assessment Badge](https://mseep.net/pr/jonaolden-pbixray-mcp-server-badge.png)](https://mseep.ai/app/jonaolden-pbixray-mcp-server)

## Info! 
Those interested in this project might also be interested in this follow-up project, [tabular-mcp](https://github.com/jonaolden/tabular-mcp), which allows running DAX queries against a local PowerBI model. Support is highly appreciated!

A [Model Context Protocol][mcp] (MCP) server for PBIXRay.

This MCP server exposes the capabilities of [PBIXRay](https://github.com/Hugoberry/pbixray) as tools and resources for LLM clients to interact with Power BI (.pbix) files.

## Features

- [x] Loading and analyzing PBIX files
- [x] Data model exploration
  - [x] Listing tables in the model
  - [x] Retrieving model metadata
  - [x] Checking model size
  - [x] Getting model statistics
  - [x] Getting comprehensive model summary
- [x] Query language access
  - [x] Viewing Power Query (M) code
  - [x] Accessing M Parameters
  - [x] Exploring DAX calculated tables
  - [x] Viewing DAX measures
  - [x] Examining DAX calculated columns
- [x] Data structure analysis
  - [x] Retrieving schema information
  - [x] Analyzing table relationships
  - [x] Accessing table contents with pagination

The list of tools is configurable, so you can choose which tools you want to make available to the MCP client.

## Tools

| Tool                  | Category  | Description                                                        |
|-----------------------|-----------|--------------------------------------------------------------------|
| `load_pbix_file`      | Core      | Load a Power BI (.pbix) file for analysis                          |
| `get_tables`          | Model     | List all tables in the model                                       |
| `get_metadata`        | Model     | Get metadata about the Power BI configuration                      |
| `get_power_query`     | Query     | Display all M/Power Query code used for data transformation        |
| `get_m_parameters`    | Query     | Display all M Parameters values                                    |
| `get_model_size`      | Model     | Get the model size in bytes                                        |
| `get_dax_tables`      | Query     | View DAX calculated tables                                         |
| `get_dax_measures`    | Query     | Access DAX measures with filtering by table or measure name        |
| `get_dax_columns`     | Query     | Access calculated column DAX expressions with filtering options    |
| `get_schema`          | Structure | Get details about the data model schema and column types           |
| `get_relationships`   | Structure | Get the details about the data model relationships                 |
| `get_table_contents`  | Data      | Retrieve the contents of a specified table with pagination         |
| `get_statistics`      | Model     | Get statistics about the model with optional filtering             |
| `get_model_summary`   | Model     | Get a comprehensive summary of the current Power BI model          |

## Requirements

- **Python 3.13** (recommended) or Python 3.10+
- uv package manager
- Windows PowerShell

### Check Your Python Version

```powershell
python --version
# Should show Python 3.13.x (recommended) or 3.10+ minimum
```

## Installation and Setup

### First Time Setup - Create Virtual Environment

```powershell
# Navigate to your project directory
cd "d:\AI\Guyen\pbixray-mcp-server-main"

# Check Python version (must be 3.10+)
python --version

# Create virtual environment with Python 3.13
uv venv --python 3.13

# Activate the virtual environment
.venv\Scripts\Activate.ps1

# Install dependencies
uv pip install mcp pbixray numpy

# Test that everything works
python src/pbixray_server.py --help
```

### Verification

Once everything is set up, you can test the server:

```powershell
# Navigate to your project directory
cd "d:\AI\Guyen\pbixray-mcp-server-main"

# Activate the virtual environment
.venv\Scripts\Activate.ps1

# Test the server
python src/pbixray_server.py --help
```

You should see output similar to:
```
usage: pbixray_server.py [-h] [--disallow DISALLOW [DISALLOW ...]] [--max-rows MAX_ROWS] [--page-size PAGE_SIZE]
                         [--load-file LOAD_FILE]
PBIXRay MCP Server
options:
  -h, --help            show this help message and exit
  --disallow DISALLOW [DISALLOW ...]
                        Specify tools to disable
  --max-rows MAX_ROWS   Maximum rows to return for table data (default: 10)
  --page-size PAGE_SIZE
                        Default page size for paginated results (default: 10)
  --load-file LOAD_FILE
                        Automatically load a PBIX file at startup
```

## Claude Desktop Configuration

### My Real Claude_Desktop_config.json
Path: `C:\Users\guyen\AppData\Roaming\Claude`

Content:
```json
{
  "mcpServers": {
    "test-server": {
      "command": "D:\\AI\\Guyen\\Claude-mcp-agentic-system\\.venv\\Scripts\\python.exe",
      "args": ["D:\\AI\\Guyen\\Claude-mcp-agentic-system\\servers\\basic_server_clean.py"],
      "env": {}
    },
    "pbixray": {
      "command": "D:\\AI\\Guyen\\pbixray-mcp-server-main\\.venv\\Scripts\\python.exe",
      "args": ["D:\\AI\\Guyen\\pbixray-mcp-server-main\\src\\pbixray_server.py"],
      "env": {}
    },
    "powerbi": {
      "command": "D:\\Projects\\powerbi-mcp-master\\.venv\\Scripts\\python.exe",
      "args": [
        "D:\\Projects\\powerbi-mcp-master\\src\\server.py"
      ],
      "env": {
        "PYTHONPATH": "D:\\Projects\\powerbi-mcp-master",
        "OPENAI_API_KEY": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
      }
    }
  }
}
```

### Alternative Configuration with PowerShell

If you prefer using PowerShell commands:

```json
{
  "mcpServers": {
    "pbixray": {
      "command": "powershell.exe",
      "args": [
        "-Command",
        "cd 'd:\\AI\\Guyen\\pbixray-mcp-server-main'; .venv\\Scripts\\Activate.ps1; python src/pbixray_server.py"
      ]
    }
  }
}
```

### Alternative Configuration with uv run

If you prefer using `uv run` (which handles the virtual environment automatically):

```json
{
  "mcpServers": {
    "pbixray": {
      "command": "powershell.exe",
      "args": [
        "-Command",
        "cd 'd:\\AI\\Guyen\\pbixray-mcp-server-main'; uv run python src/pbixray_server.py"
      ]
    }
  }
}
```

## Usage

### Windows Path Usage

When using the PBIXRay MCP Server on Windows, you can use standard Windows paths directly:

```
# Load a PBIX file using Windows path
load_pbix_file("C:\\Users\\YourName\\Documents\\file.pbix")

# Or using forward slashes (also works)
load_pbix_file("C:/Users/YourName/Documents/file.pbix")
```

### Command Line Options

The server supports several command line options:

* `--disallow [tool_names]`: Disable specific tools for security reasons
* `--max-rows N`: Set maximum number of rows returned (default: 100)
* `--page-size N`: Set default page size for paginated results (default: 20)

### Query Options

Tools support additional parameters for filtering and pagination:

#### Filtering by Name

Tools like `get_dax_measures`, `get_dax_columns`, `get_schema` and others support filtering by specific names:

```
# Get measures from a specific table
get_dax_measures(table_name="Sales")

# Get a specific measure
get_dax_measures(table_name="Sales", measure_name="Total Sales")
```

#### Pagination for Large Tables

The `get_table_contents` tool supports pagination to handle large tables efficiently:

```
# Get first page of Customer table (default 20 rows per page)
get_table_contents(table_name="Customer")

# Get second page with 50 rows per page
get_table_contents(table_name="Customer", page=2, page_size=50)
```

## Development and Testing

### Development Installation with uv

For developers working on the project:

1. Clone the repository (if not already done):
   ```powershell
   git clone https://github.com/username/pbixray-mcp.git
   cd pbixray-mcp
   ```

2. Install Python 3.13 (if needed):
   ```powershell
   uv python install 3.13
   ```

3. Create virtual environment with Python 3.13:
   ```powershell
   uv venv --python 3.13
   ```

4. Activate virtual environment:
   ```powershell
   .venv\Scripts\Activate.ps1
   ```

5. Install in development mode:
   ```powershell
   uv pip install -e .
   ```

6. Install dependencies:
   ```powershell
   uv pip install mcp pbixray numpy
   ```

### Testing with Sample Files

The repository includes sample files and test scripts to help you get started:

#### With activated virtual environment:
```powershell
# Make sure you're in the project directory and venv is activated
cd "d:\AI\Guyen\pbixray-mcp-server-main"
.venv\Scripts\Activate.ps1

# Test with sample AdventureWorks Sales.pbix file in demo/ folder
python tests/test_with_sample.py

# Try the interactive demo
python examples/demo.py

# For isolated tests of specific features
python test_pagination.py
python test_metadata_fix.py
```

#### With uv run (handles venv automatically):
```powershell
# Test with sample AdventureWorks Sales.pbix file in demo/ folder
uv run python tests/test_with_sample.py

# Try the interactive demo
uv run python examples/demo.py

# For isolated tests of specific features
uv run python test_pagination.py
uv run python test_metadata_fix.py
```

### Development Mode

To test the server during development, use the MCP Inspector:

#### With activated virtual environment:
```powershell
# Navigate to project directory
cd "d:\AI\Guyen\pbixray-mcp-server-main"

# Activate virtual environment
.venv\Scripts\Activate.ps1

# Run the MCP Inspector
mcp dev src/pbixray_server.py
```

#### With uv run (handles venv automatically):
```powershell
cd "d:\AI\Guyen\pbixray-mcp-server-main"
uv run mcp dev src/pbixray_server.py
```

This starts an interactive session where you can call tools and test responses.

### Project Structure

```
pbixray-mcp/
├── README.md            - This file
├── INSTALLATION.md      - Detailed installation instructions
├── pyproject.toml       - uv/pip configuration
├── src/                 - Source code
│   ├── __init__.py
│   └── pbixray_server.py
├── tests/               - Test scripts
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_server.py
│   └── test_with_sample.py
├── examples/            - Example scripts and configs
│   ├── demo.py
│   └── config/
├── demo/                - Sample PBIX files
│   ├── README.md
│   └── AdventureWorks Sales.pbix
└── docs/                - Additional documentation
    └── ROADMAP.md
```

## Alternative Installation Methods

### Traditional pip Installation

You can also install PBIXRay MCP Server with pip:

```powershell
pip install pbixray-mcp-server
```

For development with pip:

```powershell
python -m venv venv
venv\Scripts\activate
pip install mcp pbixray numpy
```

### WSL (Alternative)

If you prefer to use WSL, add the server configuration to your client configuration file:

```json
{
  "mcpServers": {
    "pbixray": {
      "command": "wsl.exe",
      "args": [
        "bash",
        "-c",
        "source ~/dev/pbixray-mcp/venv/bin/activate && python ~/dev/pbixray-mcp/src/pbixray_server.py"
      ]
    }
  }
}
```

#### WSL Path Conversion

When using the PBIXRay MCP Server in WSL with Claude Desktop on Windows, you need to be aware of path differences when loading PBIX files.
Windows paths (like `C:\Users\name\file.pbix`) cannot be directly accessed in WSL. Instead, use WSL paths when referencing files:
- Windows: `C:\Users\name\Downloads\file.pbix`
- WSL: `/mnt/c/Users/name/Downloads/file.pbix`

## Contributions

Contributions are much welcomed!

## Credits

* [Hugoberry](https://github.com/Hugoberry/pbixray) - Original PBIXRay library
* [rusiaaman](https://github.com/rusiaaman/wcgw) - WCGW (This MCP was fully written by Claude using wcgw)

## License

[MIT License](LICENSE)

[mcp]: https://modelcontextprotocol.io/