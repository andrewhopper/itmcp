import os
import subprocess
import asyncio
import re
import ipaddress
import logging
import shlex
from typing import List, Optional, Dict, Any, Union
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio
import dotenv
from pathlib import Path

# Load environment variables from .env file
dotenv.load_dotenv(dotenv_path=Path(__file__).parent.parent.parent / ".env")

# Configure logging
logging.basicConfig(
    filename='itmcp.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('itmcp')

# Docker execution configuration
USE_DOCKER = os.environ.get("USE_DOCKER", "true").lower() == "true"
DOCKER_CONTAINER = os.environ.get("DOCKER_CONTAINER", "itmcp_container")
logger.info(f"Docker execution: {'Enabled' if USE_DOCKER else 'Disabled'}")
logger.info(f"Docker container: {DOCKER_CONTAINER if USE_DOCKER else 'N/A'}")

# SSH credential handling
SSH_CREDENTIALS_PATH = os.environ.get("SSH_CREDENTIALS_PATH", "/app/secrets/ssh_credentials.json")
SSH_KEYS_PATH = os.environ.get("SSH_KEYS_PATH", "/app/secrets/keys")

# Function to safely load SSH credentials
def load_ssh_credentials():
    """Load SSH credentials from the credentials file."""
    try:
        import json
        if os.path.exists(SSH_CREDENTIALS_PATH):
            with open(SSH_CREDENTIALS_PATH, 'r') as f:
                return json.load(f)
        else:
            logger.warning(f"SSH credentials file not found: {SSH_CREDENTIALS_PATH}")
            return {}
    except Exception as e:
        logger.error(f"Error loading SSH credentials: {str(e)}")
        return {}

# Function to get SSH key path for a specific target
def get_ssh_key_for_target(target, user):
    """Get the SSH key path for a specific target and user."""
    credentials = load_ssh_credentials()
    target_key = f"{user}@{target}"
    
    if target_key in credentials and "key_file" in credentials[target_key]:
        key_name = credentials[target_key]["key_file"]
        key_path = os.path.join(SSH_KEYS_PATH, key_name)
        if os.path.exists(key_path):
            return key_path
    
    # Look for default key
    if "default" in credentials and "key_file" in credentials["default"]:
        key_name = credentials["default"]["key_file"]
        key_path = os.path.join(SSH_KEYS_PATH, key_name)
        if os.path.exists(key_path):
            return key_path
    
    return None

# Function to get SSH password for a specific target
def get_ssh_password_for_target(target, user):
    """Get the SSH password for a specific target and user."""
    credentials = load_ssh_credentials()
    target_key = f"{user}@{target}"
    
    if target_key in credentials and "password" in credentials[target_key]:
        return credentials[target_key]["password"]
    
    # Look for default password
    if "default" in credentials and "password" in credentials["default"]:
        return credentials["default"]["password"]
    
    return None

# Load whitelist configurations from environment variables
def get_list_from_env(env_var_name: str, default: List[str] = None) -> List[str]:
    """Parse comma-separated environment variable into a list."""
    value = os.environ.get(env_var_name, "")
    if not value and default is not None:
        return default
    return [item.strip() for item in value.split(",") if item.strip()]

# Load whitelist configurations
ALLOWED_HOSTS = get_list_from_env("ALLOWED_HOSTS", ["localhost", "127.0.0.1"])
ALLOWED_DIRECTORIES = get_list_from_env("ALLOWED_DIRECTORIES", ["/tmp"])
ALLOWED_REMOTE_COMMANDS = get_list_from_env("ALLOWED_REMOTE_COMMANDS", ["ls", "cat"])

# Log loaded configurations
logger.info(f"Loaded {len(ALLOWED_HOSTS)} allowed hosts")
logger.info(f"Loaded {len(ALLOWED_DIRECTORIES)} allowed directories")
logger.info(f"Loaded {len(ALLOWED_REMOTE_COMMANDS)} allowed remote commands")

server = Server("itmcp")

# Common utility functions
def validate_ip_address(ip: str) -> bool:
    """Validate if the string is a valid IP address."""
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

def validate_hostname(hostname: str) -> bool:
    """Basic validation for hostnames."""
    # Simple regex for hostname validation
    pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-\.]{0,61}[a-zA-Z0-9])?$'
    return bool(re.match(pattern, hostname))

def validate_target(target: str) -> bool:
    """Validate if the target is a valid IP or hostname."""
    return validate_ip_address(target) or validate_hostname(target)

def validate_whitelisted_host(hostname: str) -> bool:
    """Check if a hostname/IP is in the allowed hosts whitelist."""
    return hostname in ALLOWED_HOSTS

def validate_whitelisted_directory(directory: str) -> bool:
    """Check if a directory is in the allowed directories whitelist."""
    # Normalize the path for comparison
    normalized_path = os.path.normpath(directory)
    
    # Check if the directory is in the whitelist or is a subdirectory of a whitelisted directory
    for allowed_dir in ALLOWED_DIRECTORIES:
        allowed_dir_normalized = os.path.normpath(allowed_dir)
        if normalized_path == allowed_dir_normalized or normalized_path.startswith(allowed_dir_normalized + os.sep):
            return True
    
    return False

def validate_whitelisted_remote_command(command: str) -> bool:
    """Check if a command is in the allowed remote commands whitelist."""
    # Extract the base command (e.g., "cat" from "cat /tmp/file.txt")
    if not command:
        return False
    
    base_command = command.strip().split()[0]
    return base_command in ALLOWED_REMOTE_COMMANDS

def execute_command(command: List[str], directory: str, timeout: int = 60) -> Dict[str, Any]:
    """Execute a command and return the result."""
    logger.info(f"Executing command: {' '.join(command)} in directory: {directory}")
    
    try:
        if USE_DOCKER:
            # Prepare command to run inside Docker container
            docker_cmd = [
                "docker", "exec",
                "-w", directory,  # Set working directory inside container
                DOCKER_CONTAINER
            ]
            
            # Add the actual command to execute
            docker_cmd.extend(command)
            
            logger.info(f"Routing command through Docker: {' '.join(docker_cmd)}")
            
            result = subprocess.run(
                docker_cmd,
                shell=False,
                capture_output=True,
                text=True,
                timeout=timeout
            )
        else:
            # Execute directly on host
            result = subprocess.run(
                command,
                shell=False,  # More secure than shell=True
                cwd=directory,
                capture_output=True,
                text=True,
                timeout=timeout
            )
        
        logger.info(f"Command completed with exit code: {result.returncode}")
        
        return {
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    except subprocess.TimeoutExpired:
        logger.warning(f"Command timed out after {timeout} seconds: {' '.join(command)}")
        return {
            "exit_code": -1,
            "stdout": "",
            "stderr": f"Command timed out after {timeout} seconds"
        }
    except Exception as e:
        logger.error(f"Error executing command: {' '.join(command)}, Error: {str(e)}")
        return {
            "exit_code": -1,
            "stdout": "",
            "stderr": f"Error executing command: {str(e)}"
        }

def format_output(result: Dict[str, Any]) -> types.TextContent:
    """Format command output for display."""
    output = f"Exit code: {result['exit_code']}\n\n"
    if result["stdout"]:
        output += f"STDOUT:\n{result['stdout']}\n"
    if result["stderr"]:
        output += f"STDERR:\n{result['stderr']}\n"
    
    return types.TextContent(type="text", text=output)

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available terminal command tools."""
    return [
        types.Tool(
            name="ssh_tool",
            description="Connect to a target via SSH",
            inputSchema={
                "type": "object",
                "properties": {
                    "target": {
                        "type": "string",
                        "description": "Target hostname or IP address"
                    },
                    "user": {
                        "type": "string",
                        "description": "Username for SSH connection"
                    },
                    "port": {
                        "type": "integer",
                        "description": "SSH port (default: 22)",
                        "default": 22
                    },
                    "identity_file": {
                        "type": "string",
                        "description": "Path to SSH identity file (optional)"
                    },
                    "command": {
                        "type": "string",
                        "description": "Command to execute on the remote host (optional)"
                    }
                },
                "required": ["target", "user"]
            }
        ),
        types.Tool(
            name="ping_tool",
            description="Ping a host to check connectivity",
            inputSchema={
                "type": "object",
                "properties": {
                    "target": {
                        "type": "string",
                        "description": "Target hostname or IP address to ping"
                    },
                    "count": {
                        "type": "integer",
                        "description": "Number of ping packets to send (default: 4)",
                        "default": 4
                    }
                },
                "required": ["target"]
            }
        ),
        types.Tool(
            name="nslookup_tool",
            description="Perform DNS lookup on a hostname or IP address",
            inputSchema={
                "type": "object",
                "properties": {
                    "target": {
                        "type": "string",
                        "description": "Target hostname or IP address for DNS lookup"
                    },
                    "type": {
                        "type": "string",
                        "description": "DNS record type (default: A)",
                        "enum": ["A", "AAAA", "MX", "NS", "TXT", "SOA", "CNAME", "SRV", "PTR"],
                        "default": "A"
                    },
                    "server": {
                        "type": "string",
                        "description": "DNS server to use (optional)"
                    }
                },
                "required": ["target"]
            }
        ),
        types.Tool(
            name="telnet_tool",
            description="Test TCP connectivity to a host and port",
            inputSchema={
                "type": "object",
                "properties": {
                    "target": {
                        "type": "string",
                        "description": "Target hostname or IP address"
                    },
                    "port": {
                        "type": "integer",
                        "description": "Target port number"
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Connection timeout in seconds (default: 5)",
                        "default": 5
                    }
                },
                "required": ["target", "port"]
            }
        ),
        types.Tool(
            name="dig_tool",
            description="Perform DNS lookup with dig command",
            inputSchema={
                "type": "object",
                "properties": {
                    "target": {
                        "type": "string",
                        "description": "Target hostname or IP address for DNS lookup"
                    },
                    "type": {
                        "type": "string",
                        "description": "DNS record type (default: A)",
                        "enum": ["A", "AAAA", "MX", "NS", "TXT", "SOA", "CNAME", "SRV", "PTR"],
                        "default": "A"
                    },
                    "server": {
                        "type": "string",
                        "description": "DNS server to use (optional)"
                    },
                    "options": {
                        "type": "string",
                        "description": "Additional dig options (optional)"
                    }
                },
                "required": ["target"]
            }
        ),
        types.Tool(
            name="tcpdump_tool",
            description="Capture network packets (limited time)",
            inputSchema={
                "type": "object",
                "properties": {
                    "interface": {
                        "type": "string",
                        "description": "Network interface to capture on (e.g., eth0)"
                    },
                    "filter": {
                        "type": "string",
                        "description": "Capture filter expression (optional)"
                    },
                    "count": {
                        "type": "integer",
                        "description": "Number of packets to capture (default: 10)",
                        "default": 10
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Capture timeout in seconds (default: 10)",
                        "default": 10
                    }
                },
                "required": ["interface"]
            }
        ),
        types.Tool(
            name="ps_tool",
            description="List running processes",
            inputSchema={
                "type": "object",
                "properties": {
                    "options": {
                        "type": "string",
                        "description": "PS command options (default: aux)",
                        "default": "aux"
                    },
                    "filter": {
                        "type": "string",
                        "description": "Filter processes by pattern (optional)"
                    }
                }
            }
        ),
        types.Tool(
            name="cat_tool",
            description="Display content of a file",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file to display"
                    }
                },
                "required": ["file_path"]
            }
        ),
        types.Tool(
            name="top_tool",
            description="Display system processes (snapshot)",
            inputSchema={
                "type": "object",
                "properties": {
                    "iterations": {
                        "type": "integer",
                        "description": "Number of iterations to capture (default: 1)",
                        "default": 1
                    },
                    "delay": {
                        "type": "integer",
                        "description": "Delay between iterations in seconds (default: 1)",
                        "default": 1
                    }
                }
            }
        ),
        types.Tool(
            name="grep_tool",
            description="Search for patterns in files",
            inputSchema={
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Pattern to search for"
                    },
                    "file_path": {
                        "type": "string",
                        "description": "File or directory to search in"
                    },
                    "options": {
                        "type": "string",
                        "description": "Additional grep options (optional)"
                    }
                },
                "required": ["pattern", "file_path"]
            }
        ),
        types.Tool(
            name="head_tool",
            description="Display the beginning of a file",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file"
                    },
                    "lines": {
                        "type": "integer",
                        "description": "Number of lines to display (default: 10)",
                        "default": 10
                    }
                },
                "required": ["file_path"]
            }
        ),
        types.Tool(
            name="tail_tool",
            description="Display the end of a file",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file"
                    },
                    "lines": {
                        "type": "integer",
                        "description": "Number of lines to display (default: 10)",
                        "default": 10
                    },
                    "follow": {
                        "type": "boolean",
                        "description": "Follow the file as it grows (limited to 10 seconds)",
                        "default": False
                    }
                },
                "required": ["file_path"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: Dict[str, Any] | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool execution requests."""
    if not arguments:
        return [types.TextContent(type="text", text="Error: Missing arguments")]
    
    directory = os.path.expanduser("~")
    
    # SSH Tool
    if name == "ssh_tool":
        target = arguments.get("target")
        user = arguments.get("user")
        port = arguments.get("port", 22)
        identity_file = arguments.get("identity_file")
        command = arguments.get("command")
        
        if not validate_target(target):
            return [types.TextContent(type="text", text="Error: Invalid target")]
        
        # Check if target is in the whitelist
        if not validate_whitelisted_host(target):
            return [types.TextContent(type="text", text=f"Error: Host '{target}' is not in the allowed hosts whitelist")]
        
        # Check if command is in the whitelist (if provided)
        if command and not validate_whitelisted_remote_command(command):
            base_command = command.strip().split()[0]
            return [types.TextContent(type="text", text=f"Error: Remote command '{base_command}' is not in the allowed commands whitelist")]
        
        # Check if command targets an allowed directory (if command contains a file path)
        if command and len(command.strip().split()) > 1:
            # Check for file paths in the command arguments
            cmd_parts = command.strip().split()
            for part in cmd_parts[1:]:  # Skip the command itself
                if part.startswith('/'):  # Looks like an absolute path
                    if not validate_whitelisted_directory(part):
                        return [types.TextContent(type="text", text=f"Error: Path '{part}' is not in the allowed directories whitelist")]
        
        cmd = ["ssh"]
        
        # Add port if specified
        if port != 22:
            cmd.extend(["-p", str(port)])
        
        # Handle SSH authentication
        if identity_file:
            # User explicitly provided an identity file
            identity_path = os.path.expanduser(identity_file)
            cmd.extend(["-i", identity_path])
        else:
            # Look for stored key for this target
            key_path = get_ssh_key_for_target(target, user)
            if key_path:
                cmd.extend(["-i", key_path])
        
        # Add options for non-interactive SSH
        cmd.extend([
            "-o", "BatchMode=no",
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null"
        ])
        
        # Check if we need to use password authentication
        password = get_ssh_password_for_target(target, user)
        if password:
            # Use sshpass for password authentication
            cmd_with_password = ["sshpass", "-p", password]
            cmd_with_password.extend(cmd)
            cmd = cmd_with_password
        
        # Add user@target
        cmd.append(f"{user}@{target}")
        
        # Add command if specified
        if command:
            cmd.append(command)
        
        result = execute_command(cmd, directory, timeout=60)
        return [format_output(result)]
    
    # Ping Tool
    elif name == "ping_tool":
        target = arguments.get("target")
        count = arguments.get("count", 4)
        
        if not validate_target(target):
            return [types.TextContent(type="text", text="Error: Invalid target")]
        
        # Check if target is in the whitelist
        if not validate_whitelisted_host(target):
            return [types.TextContent(type="text", text=f"Error: Host '{target}' is not in the allowed hosts whitelist")]
        
        # Platform-specific ping command
        if os.name == "nt":  # Windows
            cmd = ["ping", "-n", str(count), target]
        else:  # Unix/Linux/macOS
            cmd = ["ping", "-c", str(count), target]
        
        result = execute_command(cmd, directory, timeout=30)
        return [format_output(result)]
    
    # NSLookup Tool
    elif name == "nslookup_tool":
        target = arguments.get("target")
        record_type = arguments.get("type", "A")
        server = arguments.get("server")
        
        if not validate_target(target):
            return [types.TextContent(type="text", text="Error: Invalid target")]
        
        # Check if target is in the whitelist
        if not validate_whitelisted_host(target):
            return [types.TextContent(type="text", text=f"Error: Host '{target}' is not in the allowed hosts whitelist")]
        
        # Check if server is in the whitelist (if provided)
        if server and not validate_whitelisted_host(server):
            return [types.TextContent(type="text", text=f"Error: DNS server '{server}' is not in the allowed hosts whitelist")]
        
        cmd = ["nslookup"]
        
        # Add record type if not A
        if record_type != "A":
            cmd.extend(["-type=" + record_type])
        
        # Add target
        cmd.append(target)
        
        # Add server if specified
        if server:
            cmd.append(server)
        
        result = execute_command(cmd, directory, timeout=30)
        return [format_output(result)]
    
    # Telnet Tool
    elif name == "telnet_tool":
        target = arguments.get("target")
        port = arguments.get("port")
        timeout = arguments.get("timeout", 5)
        
        if not validate_target(target):
            return [types.TextContent(type="text", text="Error: Invalid target")]
        
        # Check if target is in the whitelist
        if not validate_whitelisted_host(target):
            return [types.TextContent(type="text", text=f"Error: Host '{target}' is not in the allowed hosts whitelist")]
        
        # Use netcat instead of telnet for better timeout control
        if os.name == "nt":  # Windows
            cmd = ["telnet", target, str(port)]
        else:  # Unix/Linux/macOS
            cmd = ["nc", "-z", "-v", "-w", str(timeout), target, str(port)]
        
        result = execute_command(cmd, directory, timeout=timeout+5)
        return [format_output(result)]
    
    # Dig Tool
    elif name == "dig_tool":
        target = arguments.get("target")
        record_type = arguments.get("type", "A")
        server = arguments.get("server")
        options = arguments.get("options", "")
        
        if not validate_target(target):
            return [types.TextContent(type="text", text="Error: Invalid target")]
        
        # Check if target is in the whitelist
        if not validate_whitelisted_host(target):
            return [types.TextContent(type="text", text=f"Error: Host '{target}' is not in the allowed hosts whitelist")]
        
        # Check if server is in the whitelist (if provided)
        if server and not validate_whitelisted_host(server):
            return [types.TextContent(type="text", text=f"Error: DNS server '{server}' is not in the allowed hosts whitelist")]
        
        cmd = ["dig"]
        
        # Add options if specified
        if options:
            cmd.extend(shlex.split(options))
        
        # Add server if specified
        if server:
            cmd.extend(["@" + server])
        
        # Add target and record type
        cmd.append(target)
        cmd.append(record_type)
        
        result = execute_command(cmd, directory, timeout=30)
        return [format_output(result)]
    
    # TCPDump Tool
    elif name == "tcpdump_tool":
        interface = arguments.get("interface")
        filter_expr = arguments.get("filter", "")
        count = arguments.get("count", 10)
        timeout = arguments.get("timeout", 10)
        
        cmd = ["tcpdump", "-i", interface, "-n"]
        
        # Add packet count
        cmd.extend(["-c", str(count)])
        
        # Add filter if specified
        if filter_expr:
            cmd.append(filter_expr)
        
        result = execute_command(cmd, directory, timeout=timeout+5)
        return [format_output(result)]
    
    # PS Tool
    elif name == "ps_tool":
        options = arguments.get("options", "aux")
        filter_pattern = arguments.get("filter")
        
        cmd = ["ps", options]
        
        # Execute PS command
        result = execute_command(cmd, directory, timeout=10)
        
        # Apply filter if specified
        if filter_pattern and result["exit_code"] == 0:
            filter_cmd = ["grep", filter_pattern]
            filter_input = result["stdout"]
            
            try:
                filter_process = subprocess.run(
                    filter_cmd,
                    input=filter_input,
                    text=True,
                    capture_output=True
                )
                
                result["stdout"] = filter_process.stdout
                # Keep original exit code
            except Exception as e:
                result["stderr"] += f"\nError filtering output: {str(e)}"
        
        return [format_output(result)]
    
    # Cat Tool
    elif name == "cat_tool":
        file_path = arguments.get("file_path")
        
        # Expand path and do basic validation
        file_path = os.path.expanduser(file_path)
        
        if not os.path.exists(file_path):
            return [types.TextContent(type="text", text=f"Error: File not found: {file_path}")]
        
        if not os.path.isfile(file_path):
            return [types.TextContent(type="text", text=f"Error: Not a file: {file_path}")]
        
        # Check if file is in an allowed directory
        if not validate_whitelisted_directory(file_path):
            return [types.TextContent(type="text", text=f"Error: File path '{file_path}' is not in the allowed directories whitelist")]
        
        cmd = ["cat", file_path]
        result = execute_command(cmd, directory, timeout=10)
        return [format_output(result)]
    
    # Top Tool
    elif name == "top_tool":
        iterations = arguments.get("iterations", 1)
        delay = arguments.get("delay", 1)
        
        if os.name == "nt":  # Windows
            cmd = ["tasklist"]
        else:  # Unix/Linux/macOS
            cmd = ["top", "-b", "-n", str(iterations), "-d", str(delay)]
        
        result = execute_command(cmd, directory, timeout=iterations*delay+5)
        return [format_output(result)]
    
    # Grep Tool
    elif name == "grep_tool":
        pattern = arguments.get("pattern")
        file_path = arguments.get("file_path")
        options = arguments.get("options", "")
        
        # Expand path
        file_path = os.path.expanduser(file_path)
        
        # Check if file is in an allowed directory
        if not validate_whitelisted_directory(file_path):
            return [types.TextContent(type="text", text=f"Error: File path '{file_path}' is not in the allowed directories whitelist")]
        
        cmd = ["grep"]
        
        # Add options if specified
        if options:
            cmd.extend(shlex.split(options))
        
        # Add pattern and file path
        cmd.extend([pattern, file_path])
        
        result = execute_command(cmd, directory, timeout=30)
        return [format_output(result)]
    
    # Head Tool
    elif name == "head_tool":
        file_path = arguments.get("file_path")
        lines = arguments.get("lines", 10)
        
        # Expand path
        file_path = os.path.expanduser(file_path)
        
        if not os.path.exists(file_path):
            return [types.TextContent(type="text", text=f"Error: File not found: {file_path}")]
        
        if not os.path.isfile(file_path):
            return [types.TextContent(type="text", text=f"Error: Not a file: {file_path}")]
        
        # Check if file is in an allowed directory
        if not validate_whitelisted_directory(file_path):
            return [types.TextContent(type="text", text=f"Error: File path '{file_path}' is not in the allowed directories whitelist")]
        
        cmd = ["head", "-n", str(lines), file_path]
        result = execute_command(cmd, directory, timeout=10)
        return [format_output(result)]
    
    # Tail Tool
    elif name == "tail_tool":
        file_path = arguments.get("file_path")
        lines = arguments.get("lines", 10)
        follow = arguments.get("follow", False)
        
        # Expand path
        file_path = os.path.expanduser(file_path)
        
        if not os.path.exists(file_path):
            return [types.TextContent(type="text", text=f"Error: File not found: {file_path}")]
        
        if not os.path.isfile(file_path):
            return [types.TextContent(type="text", text=f"Error: Not a file: {file_path}")]
        
        # Check if file is in an allowed directory
        if not validate_whitelisted_directory(file_path):
            return [types.TextContent(type="text", text=f"Error: File path '{file_path}' is not in the allowed directories whitelist")]
        
        cmd = ["tail", "-n", str(lines)]
        
        # Add follow option if specified
        if follow:
            cmd.append("-f")
            timeout = 10  # Limit follow to 10 seconds
        else:
            timeout = 5
        
        cmd.append(file_path)
        
        result = execute_command(cmd, directory, timeout=timeout)
        return [format_output(result)]
    
    else:
        return [types.TextContent(type="text", text=f"Error: Unknown tool: {name}")]

async def main():
    # Run the server using stdin/stdout streams
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="itmcp",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
