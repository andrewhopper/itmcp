# Security Hardening Recommendations for itmcp

## Overview
This document outlines security vulnerabilities identified in the itmcp server and provides recommendations for hardening the application. itmcp allows AI assistants to execute terminal commands on a user's system, which introduces significant security risks.

## Identified Vulnerabilities

### 1. Command Injection Vulnerability
**Issue**: Using `shell=True` with `subprocess.run()` allows for command injection attacks.

**Recommendation**:
```python
# Current vulnerable code
result = subprocess.run(
    command,
    shell=True,
    # ...
)

# Hardened version
import shlex
cmd_args = shlex.split(command)
result = subprocess.run(
    cmd_args,
    shell=False,
    # ...
)
```

### 2. Restrictive Command Filtering
**Issue**: The current regex pattern only allows SSH connections to admin@192.168.0.1, but the implementation may have bypasses and lacks validation after connection.

**Recommendation**:
```python
def is_allowed_command(cmd):
    # Stricter validation
    allowed_patterns = [
        r'^ssh\s+(?:-[^\s]*\s+)*admin@192\.168\.0\.1(?:\s+-p\s+\d+)?$',
        # Add other allowed patterns if needed
    ]
    return any(re.fullmatch(pattern, cmd, re.IGNORECASE) for pattern in allowed_patterns)

if not is_allowed_command(command):
    return [types.TextContent(
        type="text",
        text="Error: Command not allowed. Only basic SSH to admin@192.168.0.1 is permitted."
    )]
```

### 3. Missing Directory Access Control
**Issue**: The code allows setting any directory with no restrictions.

**Recommendation**:
```python
def is_safe_directory(dir_path):
    # Define safe base directories
    safe_dirs = [os.path.expanduser("~/allowed_dir"), "/another/allowed/path"]
    dir_path = os.path.abspath(os.path.expanduser(dir_path))
    return any(dir_path.startswith(safe_dir) for safe_dir in safe_dirs)

directory = arguments.get("directory", "~")
expanded_dir = os.path.expanduser(directory)
if not is_safe_directory(expanded_dir):
    return [types.TextContent(
        type="text", 
        text="Error: Access to this directory is not allowed."
    )]
```

### 4. No Input Sanitization
**Issue**: No sanitization of command input beyond the SSH pattern matching.

**Recommendation**:
```python
import string

def sanitize_command(cmd):
    # Basic sanitization example - customize based on needs
    allowed_chars = string.ascii_letters + string.digits + "-_.@:/ "
    if not all(c in allowed_chars for c in cmd):
        return None
    return cmd

sanitized_command = sanitize_command(command)
if not sanitized_command:
    return [types.TextContent(
        type="text",
        text="Error: Command contains invalid characters."
    )]
```

### 5. Excessive Exception Handling
**Issue**: The broad `except Exception` could mask security issues.

**Recommendation**:
```python
except subprocess.TimeoutExpired:
    return [types.TextContent(type="text", text="Command timed out after 5 minutes")]
except subprocess.SubprocessError as e:
    return [types.TextContent(type="text", text=f"Subprocess error: {str(e)}")]
except (PermissionError, FileNotFoundError) as e:
    return [types.TextContent(type="text", text=f"Permission or path error: {str(e)}")]
except Exception as e:
    # Log the exception for security auditing
    logging.error(f"Unexpected error in command execution: {str(e)}")
    return [types.TextContent(type="text", text="An unexpected error occurred.")]
```

### 6. Add Command Logging
**Issue**: No audit logging of executed commands.

**Recommendation**:
```python
import logging

# Setup at the top of the file
logging.basicConfig(
    filename='command_audit.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

# Before executing command
logging.info(f"Executing command: {command}, directory: {directory}")

# After execution
logging.info(f"Command result: exit code {result.returncode}")
```

### 7. Rate Limiting
**Issue**: No protection against command flooding.

**Recommendation**:
```python
# At the module level
from collections import deque
import time

# Simple rate limiter - max 5 commands per minute
command_history = deque(maxlen=5)
RATE_LIMIT_WINDOW = 60  # seconds

# In the handle_call_tool function
current_time = time.time()
# Remove entries older than the window
while command_history and current_time - command_history[0] > RATE_LIMIT_WINDOW:
    command_history.popleft()

if len(command_history) >= 5:
    return [types.TextContent(
        type="text",
        text="Rate limit exceeded. Please try again later."
    )]

command_history.append(current_time)
```

### 8. Command Timeout Adjustment
**Issue**: 5-minute timeout may be excessive for simple SSH commands.

**Recommendation**:
```python
# Add to module level
DEFAULT_TIMEOUT = 60  # 1 minute instead of 5

# In the handle_call_tool function
timeout = int(os.environ.get("CMD_TIMEOUT", DEFAULT_TIMEOUT))
# Use in subprocess.run
```

## Additional Security Recommendations

1. **Implement Command Allowlisting**: Create a specific list of allowed commands rather than filtering based on patterns.

2. **Sandbox Execution**: Consider running commands in a container or sandbox environment.

3. **User Permission Restrictions**: Run the server with minimal privileges.

4. **Input Validation**: Implement thorough validation of all user inputs.

5. **Regular Security Audits**: Regularly review and test the security measures.

6. **Environment Variable Security**: Ensure sensitive information isn't exposed through environment variables.

7. **Secure Configuration**: Implement secure default settings that can be overridden only with explicit configuration.

8. **Dependency Management**: Regularly update dependencies to address security vulnerabilities.

## Conclusion
While itmcp is designed for flexibility in allowing AI assistants to execute commands, implementing these security hardening measures will significantly reduce the risk of misuse or exploitation. The tool should continue to include strong warnings about its intended use in controlled environments only. 