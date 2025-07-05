# PBIXRay MCP Server Roadmap

This document outlines the planned improvements for the PBIXRay MCP server to make it more client-agnostic, better organized, and more maintainable.

## 1. Make Implementation Client-Agnostic

Currently, the codebase contains references to specific LLM clients (notably Claude). To make the server more neutral and usable with any MCP-compatible client:

### Action Items
- [ ] Review and update all code to remove specific client references
  - [ ] Update `pbixray_server.py` to remove any client-specific assumptions
  - [ ] Rename variables, comments, and documentation to use generic "MCP client" terminology
  - [ ] Update error messages to be client-neutral
- [ ] Make the demo script work with any MCP client, not just Claude Desktop
- [ ] Reframe the server as a general-purpose "PBIXRay MCP Server" rather than a Claude extension

### Files to Modify
- `pbixray_server.py`
- `demo.py`
- `test_*.py` files
- `README.md`

## 2. Configuration Management Updates

Instead of providing an install script that directly modifies Claude Desktop configurations, provide clear instructions for manually configuring any MCP client.

### Action Items
- [ ] Remove `install_claude_desktop.py` script
- [ ] Create generic configuration examples for common MCP clients
- [ ] Update the README with client-agnostic configuration instructions
- [ ] Add a dedicated `INSTALLATION.md` file with detailed setup instructions for various clients
- [ ] Remove `claude_desktop_config.json` from the repository

### Files to Modify/Remove
- Remove: `install_claude_desktop.py`
- Remove: `claude_desktop_config.json`
- Create: `examples/config/` directory with example configs
- Update: `README.md`
- Create: `INSTALLATION.md`

## 3. Demo Directory Cleanup

Clean up the demo directory to only include relevant PBIX sample files.

### Action Items
- [ ] Remove non-PBIX files from the demo directory
  - [ ] Remove Excel files
  - [ ] Remove log files
- [ ] Add a README in the demo directory explaining the sample files
- [ ] Consider including a small, purpose-built PBIX file for testing

### Files to Modify/Remove
- Remove: `demo/Financial Sample.xlsx`
- Remove: `demo/wget-log*` files
- Create: `demo/README.md`

## 4. Project Structure Reorganization

Reorganize the project files into a cleaner, more maintainable structure.

### Action Items
- [ ] Create a `src/` directory for source code
  - [ ] Move `pbixray_server.py` to `src/`
- [ ] Create a `tests/` directory for test scripts
  - [ ] Move all test scripts to `tests/`
- [ ] Create an `examples/` directory
  - [ ] Move `demo.py` to `examples/`
  - [ ] Create example configuration snippets in `examples/config/`
- [ ] Create a `docs/` directory for documentation
  - [ ] Move this roadmap to `docs/`
  - [ ] Add additional documentation as needed
- [ ] Update imports and file references to reflect the new structure
- [ ] Add proper `__init__.py` files to make the package importable

### New Directory Structure
```
pbixray-mcp-server/
├── README.md
├── INSTALLATION.md
├── src/
│   ├── __init__.py
│   └── pbixray_server.py
├── tests/
│   ├── __init__.py
│   ├── test_server.py
│   └── test_with_sample.py
├── examples/
│   ├── demo.py
│   └── config/
│       ├── claude_desktop.json
│       └── other_clients.json
├── demo/
│   ├── README.md
│   └── AdventureWorks Sales.pbix
└── docs/
    ├── ROADMAP.md
    └── USAGE.md
```

## 5. Additional Improvements

### Action Items
- [ ] Add proper docstrings to all functions
- [ ] Implement proper logging instead of print statements
- [ ] Create a setup.py to make the package installable via pip
- [ ] Add a LICENSE file
- [ ] Add contribution guidelines in CONTRIBUTING.md
- [ ] Add version information to the server

## Timeline

1. **Phase 1: Client-Agnostic Implementation** (1-2 days)
   - Update all code to remove client-specific references
   - Update documentation to be client-neutral

2. **Phase 2: Project Reorganization** (1-2 days)
   - Create the new directory structure
   - Move files to their appropriate locations
   - Update imports and references

3. **Phase 3: Configuration and Demo Cleanup** (1 day)
   - Remove unnecessary files
   - Create example configurations
   - Update README and installation instructions

4. **Phase 4: Additional Improvements** (2-3 days)
   - Add proper documentation
   - Implement logging
   - Create setup.py
   - Add LICENSE and contribution guidelines

## Future Considerations

- Package the server for distribution via PyPI
- Add support for additional PBIX analysis features as they become available in PBIXRay
- Create a simple web UI for visualizing PBIX file content
- Add integration tests with multiple MCP clients
- Add CI/CD pipeline for automated testing and deployment
