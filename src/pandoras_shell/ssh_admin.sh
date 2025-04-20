#!/bin/bash
#
# Simple wrapper script to connect to admin@192.168.0.1 via SSH
#

# Default parameters
SSH_PORT=22
IDENTITY_FILE=""

# Display usage information
function show_usage {
    echo "Usage: $0 [OPTIONS] [COMMAND]"
    echo
    echo "Connect to admin@192.168.0.1 via SSH and optionally execute a command."
    echo
    echo "Options:"
    echo "  -i, --identity FILE     Use identity file for authentication"
    echo "  -p, --port PORT         SSH port (default: 22)"
    echo "  -h, --help              Display this help message"
    echo
    echo "Example:"
    echo "  $0                       # Connect to SSH shell"
    echo "  $0 'ls -la'              # Run command and exit"
    echo "  $0 -i ~/.ssh/id_rsa      # Connect using specific identity file"
    exit 1
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        -i|--identity)
            IDENTITY_FILE="$2"
            shift 2
            ;;
        -p|--port)
            SSH_PORT="$2"
            shift 2
            ;;
        -h|--help)
            show_usage
            ;;
        *)
            # Remaining arguments are the command to execute
            break
            ;;
    esac
done

# Build the SSH command
SSH_CMD="ssh -p $SSH_PORT"

# Add identity file if specified
if [ -n "$IDENTITY_FILE" ]; then
    SSH_CMD="$SSH_CMD -i $IDENTITY_FILE"
fi

# Add the target host
SSH_CMD="$SSH_CMD admin@192.168.0.1"

# Add command if provided
if [ $# -gt 0 ]; then
    SSH_CMD="$SSH_CMD $*"
fi

# Execute the SSH command
exec $SSH_CMD 