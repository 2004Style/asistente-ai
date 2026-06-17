# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-06-15

### Added
- Fully integrated SQLite, FileSystem, Chroma, and Qdrant vector memory store backends.
- Concrete operating system adapters for Debian, Fedora, GNOME, KDE, macOS, and Windows.
- Standard desktop control tools for cursor movement, clicking, scrolling, typing, shortcuts, and application management.
- Command-line interface with `run`, `start`, `stop`, `restart`, `status`, and `install` commands.
- Secure terminal command runner sandbox protecting path traversal and environment variables.
- Structured YAML configuration loader and schema validator.
- Diagnostic health monitoring endpoint (`/health`).
