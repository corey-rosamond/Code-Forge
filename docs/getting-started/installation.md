# Installation Guide

## Requirements

- Python 3.11 or higher
- pip or pipx for installation
- OpenRouter API key

## Installation Methods

### Using pip

```bash
pip install forge
```

### Using pipx (Recommended)

```bash
pipx install forge
```

pipx installs in an isolated environment, avoiding dependency conflicts.

### From Source

```bash
git clone https://github.com/anthropics/forge.git
cd forge
pip install -e ".[dev]"
```

## Configuration

### API Key Setup

Set your OpenRouter API key as an environment variable:

```bash
export OPENROUTER_API_KEY="your-api-key"
```

You can get an API key from [OpenRouter](https://openrouter.ai).

### Configuration File

Create a configuration file at `~/.config/forge/config.yaml`:

```yaml
model:
  default: "anthropic/claude-3-sonnet"
  max_tokens: 8192
  temperature: 1.0

display:
  theme: dark

session:
  auto_save: true
  auto_save_interval: 60
```

See [Configuration Reference](../reference/configuration.md) for all options.

## Verify Installation

```bash
forge --version
```

You should see the version number printed.

## First Run

```bash
forge
```

This starts the interactive REPL. Type `/help` to see available commands.

## Troubleshooting

### Missing Dependencies

If you encounter import errors:

```bash
pip install forge[all]
```

### Permission Errors

On Linux/macOS, if you get permission errors:

```bash
pip install --user forge
```

### API Key Not Found

If you see "API key not configured":

1. Verify the environment variable is set:
   ```bash
   echo $OPENROUTER_API_KEY
   ```

2. Or set it in the config file:
   ```yaml
   # ~/.config/forge/config.yaml
   api_key: "your-api-key"  # Not recommended for security
   ```
