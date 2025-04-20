# itmcp

⚠️ **IMPORTANT SECURITY WARNING**: This MCP server grants AI assistants unrestricted ability to execute terminal commands on your system. **Only use in controlled environments like virtual machines (VMs) or development systems you can afford to rebuild.**

## About

An MCP server that empowers AI assistants to execute terminal commands on your system. Due to the unrestricted access this provides, it's crucial to use this software responsibly and be fully aware of the security risks involved.

**Note**: This server is compatible with any AI assistant that supports the Model Context Protocol (MCP). The provided configuration and setup instructions are specifically tailored for Claude Desktop, which offers comprehensive support for all MCP features.

## Features

- Execute any shell command with full system access
- Capture command output (stdout/stderr)
- Set working directory
- Handle command timeouts
- Enterprise-grade security with session management and audit logging
- High scalability supporting 10,000+ users
- Optimized for 200ms response times

## API

### Tools

- **execute_command**
  - Execute any shell command and return its output
  - **Inputs**:
    - `command` (string): Command to execute
    - `directory` (string, optional): Working directory
  - **Returns**:
    - Command exit code
    - Standard output
    - Standard error
  - **Features**:
    - 5-minute timeout
    - Working directory support
    - Error handling

## Installation

### Prerequisites

- **Claude Desktop** with an active Claude Pro/Enterprise subscription
  - Download from: [Claude AI](https://claude.ai/download)
- **Python 3.10** or higher
- **Git**
- **uv** (required for package management)

# Windows Installation

1. Install Prerequisites:
   
   **Option A** - Using winget (if available on your system):
   ```powershell
   winget install python git
   ```

   **Option B** - Manual installation (recommended):
   - Download and install Python from [python.org](https://www.python.org)
   - Download and install Git from [git-scm.com](https://git-scm.com)

2. Install uv:

   Open Command Prompt (`cmd.exe`) as administrator and run:
   ```powershell
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

   If you encounter any issues, you may need to restart your terminal or computer for the changes to take effect.

3. Clone and set up the project:
   ```cmd
   git clone https://github.com/andrewhopper/itmcp.git
   cd itmcp
   ```

   Then create a virtual environment. Try these commands in order until one works:
   ```cmd
   python -m venv venv
   ```

   If that doesn't work, try:
   ```cmd
   python3 -m venv venv
   ```

   Then activate the environment:
   ```cmd
   venv\Scripts\activate
   ```

4. Install dependencies:
   ```cmd
   uv pip install mcp
   pip install -e .
   ```

**Note**: If you installed Python from [python.org](https://www.python.org), you'll typically use `python`. If you installed via winget or from the Microsoft Store, you might need to use `python3`. Try both commands if one doesn't work.

### macOS Installation

1. Install Prerequisites:
   ```bash
   brew install python git uv
   ```

2. Clone and set up the project:
   ```bash
   git clone https://github.com/andrewhopper/itmcp.git
   cd itmcp
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   uv pip install mcp
   pip install -e .
   ```

## Configuration

### Whitelist Configuration

itmcp uses a configuration system to restrict which hosts, directories, and commands can be executed. These configurations are stored in the `config.yaml` file in the project root directory.

Example configuration:

```yaml
# Allowed hosts configuration
allowed_hosts:
  - 192.168.0.1
  - localhost
  - 127.0.0.1
  - example.com

# Allowed directories configuration
allowed_directories:
  - /tmp
  - /var/log
  - /home/admin/logs

# Allowed remote commands configuration
allowed_remote_commands:
  - ls
  - cat
  - grep
  - head
  - tail
  - df
  - du
  - uname
```

If the `config.yaml` file is not found or specific settings are missing, the system will default to a minimal set of safe values:
- Allowed hosts: localhost, 127.0.0.1
- Allowed directories: /tmp
- Allowed remote commands: ls, cat

These restrictions ensure that:
1. SSH connections are only made to whitelisted hosts
2. File operations only access whitelisted directories
3. Remote commands are limited to a predefined set of safe operations

### Enterprise Security Features

itmcp implements enterprise-grade security features:

1. **Session Management**
   - Automatic session tracking and expiration
   - Protection against session hijacking
   - Secure session storage

2. **Audit Logging**
   - Comprehensive logging of all executed commands
   - User activity tracking
   - Security event monitoring
   - Log rotation and archiving

3. **Performance Targets**
   - Optimized for 200ms response times
   - Scalable to support 10,000+ concurrent users
   - Efficient resource management

### Claude Desktop Configuration

Locate the correct configuration directory - try these paths in order:

1. `%APPDATA%\Claude\` (typically `C:\Users\[YourUsername]\AppData\Roaming\Claude\`)
2. `%LOCALAPPDATA%\AnthropicClaude\` (typically `C:\Users\[YourUsername]\AppData\Local\AnthropicClaude\`)

Create or edit `claude_desktop_config.json` in the correct directory:

```json
{
  "mcpServers": {
    "itmcp": {
      "command": "C:/path/to/cloned/itmcp/venv/Scripts/python.exe",
      "args": [
        "C:/path/to/cloned/itmcp/src/itmcp/executor.py"
      ],
      "env": {
        "PYTHONPATH": "C:/path/to/cloned/itmcp/src"
      }
    }
  }
}
```

#### Important Notes for Windows:

- Use forward slashes (`/`) in paths, not backslashes (`\`)
- Replace `[YourUsername]` with your actual Windows username
- File must be named exactly `claude_desktop_config.json`
- If both possible config locations exist, try each until successful

### macOS

Create or edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "itmcp": {
      "command": "/path/to/cloned/itmcp/venv/bin/python",
      "args": [
        "/path/to/cloned/itmcp/src/itmcp/executor.py"
      ],
      "env": {
        "PYTHONPATH": "/path/to/cloned/itmcp/src"
      }
    }
  }
}
```

#### Important Notes for macOS:

- Replace `[YourUsername]` with your actual username
- You can use `$HOME` instead of `/Users/[YourUsername]` if preferred
- File must be named exactly `claude_desktop_config.json`
- The `command` path should point to the Python interpreter inside your virtual environment (`venv/bin/python`), not the system Python

### After Configuration

1. Restart Claude Desktop completely (quit/exit, not just close the window).
2. Click the 🔌 icon to verify the server appears in the "Installed MCP Servers" list.
3. If the server doesn't appear, check Claude's logs:
   - **Windows**: `%APPDATA%\Claude\Logs\mcp*.log` or `%LOCALAPPDATA%\AnthropicClaude\Logs\mcp*.log`
   - **macOS**: `~/Library/Logs/Claude/mcp*.log`

## Security Considerations

This server executes commands with your user privileges. **Take these precautions:**

- Use **only** in VMs or disposable development environments.
- **Never** use on production systems or machines with sensitive data.
- Consider implementing command restrictions if needed.
- Monitor system access and activity.
- Keep backups of important data.
- Review audit logs regularly to detect suspicious activity.
- Use session management features to limit exposure.

**Disclaimer**: The developers are not responsible for any damages or losses resulting from the use of this software. Use it at your own risk.

## Project Conventions

This project follows these conventions:

- File and directory names use lowercase with hyphens
- Project structure follows the standard layout with `/src`, `/docs`, `/tests`, `/config`
- Code follows language-specific style guides with consistent indentation
- Documentation includes file IDs for traceability
- Security features are implemented at enterprise level

## Target Users

itmcp is designed for:

- System administrators and IT professionals using CLI tools for troubleshooting
- Information security professionals
- IT security teams
- Hackers and penetration testers

## Troubleshooting

If you encounter issues:

1. **Check logs:**
   - **Windows**: `%APPDATA%\Claude\Logs\mcp*.log` or `%LOCALAPPDATA%\AnthropicClaude\Logs\mcp*.log`
   - **macOS**: `~/Library/Logs/Claude/mcp*.log`

2. **Verify installation:**
   - Ensure `uv` is properly installed and in your PATH.
   - Check that `mcp` package is installed: `pip show mcp`.
   - Verify Python version is 3.10 or higher.

3. **Configuration issues:**
   - Double-check all paths in `claude_desktop_config.json`.
   - Verify JSON syntax is valid.
   - Ensure proper path separators for your OS.
   - Confirm config file is in the correct location.

4. **Environment issues:**
   - Make sure `virtualenv` is activated if using one.
   - Verify `PYTHONPATH` is set correctly.
   - Check file permissions.

5. **Test server manually:**
   ```bash
   # First, make sure you're in the itmcp directory:
   cd /path/to/cloned/itmcp
   
   # For macOS:
   ./venv/bin/python src/itmcp/executor.py
   
   # For Windows:
   .\venv\Scripts\python.exe src\itmcp\executor.py

   # The executor will appear to hang with no output - this is normal.
   # It's waiting for connections from Claude Desktop.
   # Use Ctrl+C to stop it.
   ```

6. **Connection issues:**
   - If you get "Could not connect to MCP server" errors, ensure you're using the virtual environment's Python interpreter in your config file.
   - For macOS: Use `/path/to/cloned/itmcp/venv/bin/python`
   - For Windows: Use `C:/path/to/cloned/itmcp/venv/Scripts/python.exe`

## Testing

After setup, try these commands in Claude Desktop:

```text
Can you run 'pwd' and tell me what directory we're in?
```

or

```text
Can you list the files in my home directory? Which of them are larger than 200 MB?
```

## Attribution

This project is a fork of [itmcp](https://github.com/andrewhopper/itmcp) by Christian Hägg, used under the [MIT License](LICENSE). The original repository can be found at https://github.com/andrewhopper/itmcp.git.
