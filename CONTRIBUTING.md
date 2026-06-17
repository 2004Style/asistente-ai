# Contributing to rbot

Thank you for your interest in contributing to rbot!

## Development Environment Setup

1. Clone the repository.
2. Initialize virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
3. Install development dependencies:
   ```bash
   pip install -e .
   ```
4. Run the test suite:
   ```bash
   pytest
   ```

## Adding New Features

- **New Tools**: Implement your action under a subfolder in `tools/` and inherit from `BaseTool`, register the manifest, and add it to `load_default_tools` in `tools/registry.py`.
- **New Platforms**: Implement a desktop or distro adapter matching the interfaces in `host/adapters/base.py`.
