---
id: DOC-config-guidelines-001
created: 2023-05-22
---

# Configuration Guidelines for itmcp

This document outlines the configuration options and best practices for setting up itmcp with enterprise-grade security features.

## Configuration File Structure

itmcp uses a YAML-based configuration system stored in the `config.yaml` file in the project root directory. This file contains critical security settings and should be properly configured before deployment.

### Basic Configuration Structure

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
```

## Configuration Options

### Host Restrictions

The `allowed_hosts` section defines which hosts can be accessed through the shell:

```yaml
allowed_hosts:
  - localhost
  - 127.0.0.1
  - internal-server.local
  - 192.168.1.100
```

**Security Considerations:**
- Only include hosts that are necessary for your operations
- Use internal hostnames or IP addresses rather than public endpoints
- For development, limit to `localhost` and `127.0.0.1`

### Directory Restrictions

The `allowed_directories` section defines which file system directories can be accessed:

```yaml
allowed_directories:
  - /tmp
  - /var/log
  - /home/admin/logs
  - /etc/config
```

**Security Considerations:**
- Avoid adding sensitive directories (e.g., `/etc/`, `/home/user/`)
- Use specific subdirectories rather than parent directories
- Consider using read-only directories for logs and configurations

### Command Restrictions

The `allowed_remote_commands` section defines which shell commands can be executed:

```yaml
allowed_remote_commands:
  - ls
  - cat
  - grep
  - head
  - tail
  - df
  - du
  - uname
  - ps
  - top
```

**Security Considerations:**
- Only include non-destructive commands
- Avoid commands that can modify the system (e.g., `rm`, `mv`, `chmod`)
- Consider the impact of each command before adding it

## Enterprise Security Features

### Session Management

Session management is configured automatically but can be fine-tuned with these parameters in the configuration:

```yaml
session_management:
  timeout_minutes: 30
  max_inactive_time: 15
  max_sessions_per_user: 3
```

**Configuration Options:**
- `timeout_minutes`: Maximum lifetime of a session (default: 30)
- `max_inactive_time`: Minutes of inactivity before session expiration (default: 15)
- `max_sessions_per_user`: Maximum concurrent sessions per user (default: 3)

### Audit Logging

Audit logging captures all activity within the shell:

```yaml
audit_logging:
  enabled: true
  log_level: INFO
  log_format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  log_file: "/var/log/itmcp/audit.log"
  log_rotation: true
  rotation_size_mb: 10
  retention_days: 90
```

**Configuration Options:**
- `enabled`: Enable/disable audit logging (default: true)
- `log_level`: Logging verbosity (DEBUG, INFO, WARNING, ERROR)
- `log_format`: Format string for log entries
- `log_file`: Path to the audit log file
- `log_rotation`: Enable log rotation to manage file sizes
- `rotation_size_mb`: Maximum log file size before rotation
- `retention_days`: Number of days to retain log files

### Performance Configuration

Performance settings to meet the 200ms response time target with high user loads:

```yaml
performance:
  max_threads: 50
  request_timeout_ms: 200
  max_concurrent_requests: 5000
  connection_pool_size: 100
  memory_limit_mb: 1024
```

**Configuration Options:**
- `max_threads`: Maximum worker threads (default: based on CPU cores)
- `request_timeout_ms`: Request timeout in milliseconds (default: 200)
- `max_concurrent_requests`: Maximum concurrent requests (default: 5000)
- `connection_pool_size`: Size of the connection pool (default: 100)
- `memory_limit_mb`: Maximum memory usage in MB (default: 1024)

## Default Values

If `config.yaml` is not found or specific settings are missing, the system will default to these safe values:

- **allowed_hosts**: localhost, 127.0.0.1
- **allowed_directories**: /tmp
- **allowed_remote_commands**: ls, cat

## Configuration Validation

The system performs validation checks on your configuration file at startup:

1. **Syntax Validation**: Ensures the YAML file is properly formatted
2. **Security Validation**: Checks for security misconfigurations
3. **Dependency Validation**: Verifies all required components are available
4. **Performance Validation**: Tests if performance targets can be met

If validation fails, detailed error messages will be logged, and the server may default to safe configurations or refuse to start depending on the severity of the issue. 