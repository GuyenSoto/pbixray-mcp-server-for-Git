# Contributing to PBIXRay MCP Server

We love your input! We want to make contributing to PBIXRay MCP Server as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features
- Becoming a maintainer

## Development Process

We use GitHub to host code, to track issues and feature requests, as well as accept pull requests.

### Pull Requests

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Pull Request Requirements

- Update the README.md with details of changes to the interface, if applicable
- Update the documentation with details of any new features or changes
- The PR should work for Python 3.8 and above
- Ensure all tests pass

## Issues and Feature Requests

We use GitHub issues to track public bugs and feature requests. Please ensure your description is clear and has sufficient instructions to be able to reproduce the issue.

## License

By contributing, you agree that your contributions will be licensed under the project's MIT License.

## Development Environment Setup

### Setting Up Your Development Environment

1. Clone the repository:
   ```bash
   git clone https://github.com/username/pbixray-mcp.git
   cd pbixray-mcp
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install development dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install the package in development mode:
   ```bash
   pip install -e .
   ```

### Running Tests

Run tests using:

```bash
python -m tests.test_with_sample
```

## Code Style

We use [PEP 8](https://www.python.org/dev/peps/pep-0008/) for code style and [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html) for docstrings.

## References

- [PBIXRay documentation](https://github.com/Hugoberry/pbixray)
- [Model Context Protocol documentation](https://modelcontextprotocol.io/)
