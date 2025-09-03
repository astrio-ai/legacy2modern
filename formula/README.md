# Homebrew Formula for Legacy2Modern Web

This directory contains the Homebrew formula for installing Legacy2Modern Web via Homebrew.

## Formula File

- `legacy2modern-web.rb` - The Homebrew formula for installing the CLI

## Installation via Homebrew

Once the formula is available in a Homebrew tap, users can install the CLI with:

```bash
# Install the CLI
brew install legacy2modern-web

# Verify installation
legacy2modern-web --help
l2m-web --help
```

## Features

The Homebrew formula provides:

- **Easy Installation**: One-command installation via Homebrew
- **Dependency Management**: Automatic Python 3.10+ dependency installation
- **Multiple Commands**: Both `legacy2modern-web` and `l2m-web` commands available
- **Automatic Updates**: Easy updates via `brew upgrade legacy2modern-web`

## Requirements

- macOS (Homebrew is primarily for macOS)
- Python 3.10 or higher
- Internet connection for downloading dependencies

## Uninstallation

To uninstall via Homebrew:

```bash
brew uninstall legacy2modern-web
```

## Development

To test the formula locally:

```bash
# Install from local formula
brew install --build-from-source ./formula/legacy2modern-web.rb

# Test the installation
legacy2modern-web --help
```

## Publishing

To make the formula available to users:

1. Create a Homebrew tap repository
2. Add this formula to the tap
3. Users can then install with: `brew install your-tap/legacy2modern-web`

## Formula Details

The formula:
- Installs Python dependencies via pip
- Creates executable scripts for `legacy2modern-web` and `l2m-web` commands
- Includes test commands to verify installation
- Supports both stable releases and HEAD (development) versions 