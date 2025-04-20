# ITMCP

Secure network administration tools for AI assistants through the Model Context Protocol (MCP).

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

## Overview

ITMCP is an MCP server that enables AI assistants to safely execute networking commands inside a Docker container sandbox. It provides a secure interface for running common network diagnostic and administration tools while maintaining strict security controls.

The project implements the Model Context Protocol (MCP) to expose networking tools as callable functions for AI assistants, allowing them to perform network diagnostics and system administration tasks in a controlled environment.

## Features

- **Docker Isolation**: All commands run in a sandboxed Docker container for enhanced security
- **Security Controls**: Comprehensive whitelisting of hosts, directories, and commands
- **Network Diagnostic Tools**: SSH, ping, nslookup, telnet, dig, tcpdump, and more
- **File Operations**: Secure access to view and analyze files with tools like cat, grep, head, tail
- **Process Management**: View running processes with ps and top tools
- **Credential Management**: Secure handling of SSH keys and passwords
- **MCP Integration**: Full compatibility with the Model Context Protocol
- **Enterprise-Grade Security**: Session management, audit logging, and access controls

## Installation

### Prerequisites

- Python 3.10 or higher
- Docker (for containerized execution)
- MCP library (version 1.0.0 or higher)

### Basic Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/itmcp.git
   cd itmcp
   ```

2. Install dependencies:
   ```bash
   pip install -e .
   ```

### Docker Setup

1. Build the Docker container:
   ```bash
   docker build -t itmcp_container .
   ```

2. Run the container:
   ```bash
   docker-compose up -d
   ```

## Configuration

ITMCP uses a YAML-based configuration system and environment variables for setup.

### Environment Variables

Create a `.env` file in the project root with the following variables:

```
# Docker configuration
USE_DOCKER=true
DOCKER_CONTAINER=itmcp_container

# SSH credentials configuration
SSH_CREDENTIALS_PATH=/app/secrets/ssh_credentials.json
SSH_KEYS_PATH=/app/secrets/keys

# Security whitelists
ALLOWED_HOSTS=localhost,127.0.0.1,example.com
ALLOWED_DIRECTORIES=/tmp,/var/log
ALLOWED_REMOTE_COMMANDS=ls,cat,grep
```

### Security Whitelists

ITMCP implements three key whitelists for security:

1. **Allowed Hosts**: Restricts which hosts can be targeted by network tools
2. **Allowed Directories**: Limits file system access to specific directories
3. **Allowed Remote Commands**: Controls which commands can be executed remotely

## Available Tools

ITMCP provides the following network administration tools:

| Tool | Description |
|------|-------------|
| `ssh_tool` | Connect to a target via SSH |
| `ping_tool` | Ping a host to check connectivity |
| `nslookup_tool` | Perform DNS lookup on a hostname or IP address |
| `telnet_tool` | Test TCP connectivity to a host and port |
| `dig_tool` | Perform DNS lookup with dig command |
| `tcpdump_tool` | Capture network packets (limited time) |
| `ps_tool` | List running processes |
| `cat_tool` | Display content of a file |
| `top_tool` | Display system processes (snapshot) |
| `grep_tool` | Search for patterns in files |
| `head_tool` | Display the beginning of a file |
| `tail_tool` | Display the end of a file |

## Security Features

ITMCP implements enterprise-grade security features:

### Session Management

- Secure session creation with cryptographic tokens
- Session expiration and timeout controls
- Concurrent session limits
- Session validation and regeneration

### Audit Logging

- Comprehensive command logging
- User attribution for all actions
- Success/failure logging
- Security event flagging
- Tamper-evident logs

### Access Control

- Command whitelisting
- Directory restrictions
- Host restrictions
- Input validation and sanitization

## Docker Integration

ITMCP uses Docker to create a secure sandbox for command execution:

1. All commands are routed through the Docker container
2. The container has limited access to the host system
3. Resource limits can be applied to prevent abuse
4. Network isolation provides an additional security layer

## Usage Examples

### MCP Configuration

#### Claude Desktop Configuration

To use ITMCP with Claude desktop, add the following to your `config.json` file:

```json
{
  "servers": [
    {
      "name": "itmcp",
      "command": ["python", "-m", "itmcp.server"],
      "environment": {
        "USE_DOCKER": "true",
        "DOCKER_CONTAINER": "itmcp_container",
        "ALLOWED_HOSTS": "localhost,127.0.0.1,yahoo.com,firewall.local"
      }
    }
  ]
}
```

#### Cline Configuration

For Cline AI, a more detailed configuration is provided in the `mcp-config.json` file included in this repository:

```json
{
    "servers": [
        {
            "name": "itmcp",
            "command": [
                "python",
                "-m",
                "itmcp.server"
            ],
            "environment": {
                "USE_DOCKER": "true",
                "DOCKER_CONTAINER": "itmcp_container",
                "ALLOWED_HOSTS": "localhost,127.0.0.1,yahoo.com,firewall.local",
                "ALLOWED_DIRECTORIES": "/tmp,/var/log",
                "ALLOWED_REMOTE_COMMANDS": "ls,cat,grep,ping,ssh,nslookup,dig,telnet,tcpdump,ps,top,head,tail"
            },
            "description": "Secure network administration tools running in a Docker sandbox",
            "tools": [
                {
                    "name": "ssh_tool",
                    "description": "Connect to a target via SSH"
                },
                {
                    "name": "ping_tool",
                    "description": "Ping a host to check connectivity"
                },
                {
                    "name": "nslookup_tool",
                    "description": "Perform DNS lookup on a hostname or IP address"
                },
                {
                    "name": "telnet_tool",
                    "description": "Test TCP connectivity to a host and port"
                },
                {
                    "name": "dig_tool",
                    "description": "Perform DNS lookup with dig command"
                },
                {
                    "name": "tcpdump_tool",
                    "description": "Capture network packets (limited time)"
                },
                {
                    "name": "ps_tool",
                    "description": "List running processes"
                },
                {
                    "name": "cat_tool",
                    "description": "Display content of a file"
                },
                {
                    "name": "top_tool",
                    "description": "Display system processes (snapshot)"
                },
                {
                    "name": "grep_tool",
                    "description": "Search for patterns in files"
                },
                {
                    "name": "head_tool",
                    "description": "Display the beginning of a file"
                },
                {
                    "name": "tail_tool",
                    "description": "Display the end of a file"
                }
            ]
        }
    ]
}
```

To use this configuration with Cline:

1. Copy the `mcp-config.json` file to your Cline configuration directory
2. Start Cline with the `--mcp-config` flag pointing to this file
3. The ITMCP tools will be available for use in your Cline sessions

### Example 1: Ping a Host

```
# Using the ping_tool to check connectivity to yahoo.com
<use_mcp_tool>
<server_name>itmcp</server_name>
<tool_name>ping_tool</tool_name>
<arguments>
{
  "target": "yahoo.com",
  "count": 4
}
</arguments>
</use_mcp_tool>
```

### Example 2: SSH Connection to Firewall

```
# Using the ssh_tool to connect to a firewall and run a command
<use_mcp_tool>
<server_name>itmcp</server_name>
<tool_name>ssh_tool</tool_name>
<arguments>
{
  "target": "firewall.local",
  "user": "admin",
  "command": "show interface status"
}
</arguments>
</use_mcp_tool>
```

### Example 3: DNS Lookup

```
# Using the dig_tool to perform a DNS lookup
<use_mcp_tool>
<server_name>itmcp</server_name>
<tool_name>dig_tool</tool_name>
<arguments>
{
  "target": "yahoo.com",
  "type": "MX"
}
</arguments>
</use_mcp_tool>
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Author

**Andrew Hopper**

- Email: hopperab@gmail.com
- Twitter: [x.com/andrewhopper](https://x.com/andrewhopper)
- Website: [andyhop.316.dev](https://andyhop.316.dev)
- LinkedIn: [linkedin.com/in/andrewhopper](https://linkedin.com/in/andrewhopper)

## Security Considerations

ITMCP is designed with security in mind, but proper configuration is essential:

- Always run in a Docker container for isolation
- Carefully configure whitelists for hosts, directories, and commands
- Regularly review audit logs for suspicious activity
- Keep the system updated with security patches
- Follow the security best practices in the documentation
