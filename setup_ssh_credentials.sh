#!/bin/bash

# Script to set up SSH credentials for the itmcp container
# This will allow for both password-based and key-based authentication to remote systems

set -e

SECRETS_DIR="./secrets"
KEYS_DIR="$SECRETS_DIR/keys"
CREDENTIALS_FILE="$SECRETS_DIR/ssh_credentials.json"

# Create secrets directory if it doesn't exist
mkdir -p "$KEYS_DIR"
chmod 700 "$SECRETS_DIR"
chmod 700 "$KEYS_DIR"

# Check if the credentials file exists, if not create it
if [ ! -f "$CREDENTIALS_FILE" ]; then
  echo '{}' > "$CREDENTIALS_FILE"
  chmod 600 "$CREDENTIALS_FILE"
fi

# Function to add a new SSH key entry
add_key_entry() {
  local target_user="$1"
  local key_file="$2"
  local key_basename=$(basename "$key_file")
  
  # Copy the key to the keys directory
  cp "$key_file" "$KEYS_DIR/$key_basename"
  chmod 600 "$KEYS_DIR/$key_basename"
  
  # Update the credentials file - using a properly escaped key
  local escaped_key=$(echo "$target_user" | sed 's/[@\.]/\\&/g')
  jq --arg key "$target_user" --arg value "$key_basename" '.[$key] = {"key_file": $value}' "$CREDENTIALS_FILE" > tmp.json && mv tmp.json "$CREDENTIALS_FILE"
  chmod 600 "$CREDENTIALS_FILE"
  
  echo "Added key $key_basename for $target_user"
}

# Function to add a new SSH password entry
add_password_entry() {
  local target_user="$1"
  local password="$2"
  
  # Update the credentials file - using --arg to handle special chars properly
  jq --arg key "$target_user" --arg value "$password" '.[$key] = {"password": $value}' "$CREDENTIALS_FILE" > tmp.json && mv tmp.json "$CREDENTIALS_FILE"
  chmod 600 "$CREDENTIALS_FILE"
  
  echo "Added password for $target_user"
}

# Function to generate a new SSH key
generate_key() {
  local target_user="$1"
  local key_name="${target_user//[@\.:]/_}.key"
  
  # Generate a new key
  ssh-keygen -t ed25519 -f "$KEYS_DIR/$key_name" -N "" -C "itmcp_generated_key_for_$target_user"
  chmod 600 "$KEYS_DIR/$key_name"
  
  # Update the credentials file - using --arg to handle special chars properly
  jq --arg key "$target_user" --arg value "$key_name" '.[$key] = {"key_file": $value}' "$CREDENTIALS_FILE" > tmp.json && mv tmp.json "$CREDENTIALS_FILE"
  chmod 600 "$CREDENTIALS_FILE"
  
  echo "Generated new key $key_name for $target_user"
  echo "Public key:"
  cat "$KEYS_DIR/$key_name.pub"
  echo ""
  echo "You'll need to add this public key to the authorized_keys file on your remote server"
}

# Function to show the current credentials
show_credentials() {
  echo "Current SSH credentials:"
  jq 'keys' "$CREDENTIALS_FILE"
}

# Check if jq is installed
if ! command -v jq &> /dev/null; then
  echo "Error: jq is required for this script to work"
  echo "On Ubuntu/Debian: apt-get install jq"
  echo "On macOS: brew install jq"
  exit 1
fi

# Parse command line arguments
if [ $# -eq 0 ]; then
  echo "Usage: $0 [command] [arguments]"
  echo ""
  echo "Commands:"
  echo "  add-key <user@host> <key_file>    Add a key for a specific user and host"
  echo "  add-password <user@host>          Add a password for a specific user and host (will prompt)"
  echo "  generate-key <user@host>          Generate a new SSH key for a specific user and host"
  echo "  set-default-key <key_file>        Set a default key to use when no specific key is found"
  echo "  set-default-password              Set a default password to use when no specific password is found"
  echo "  show                              Show current credentials"
  exit 1
fi

COMMAND="$1"
shift

case "$COMMAND" in
  add-key)
    if [ $# -ne 2 ]; then
      echo "Usage: $0 add-key <user@host> <key_file>"
      exit 1
    fi
    add_key_entry "$1" "$2"
    ;;
  add-password)
    if [ $# -ne 1 ]; then
      echo "Usage: $0 add-password <user@host>"
      exit 1
    fi
    echo -n "Enter password for $1: "
    read -s PASSWORD
    echo ""
    add_password_entry "$1" "$PASSWORD"
    ;;
  generate-key)
    if [ $# -ne 1 ]; then
      echo "Usage: $0 generate-key <user@host>"
      exit 1
    fi
    generate_key "$1"
    ;;
  set-default-key)
    if [ $# -ne 1 ]; then
      echo "Usage: $0 set-default-key <key_file>"
      exit 1
    fi
    add_key_entry "default" "$1"
    ;;
  set-default-password)
    echo -n "Enter default password: "
    read -s PASSWORD
    echo ""
    add_password_entry "default" "$PASSWORD"
    ;;
  show)
    show_credentials
    ;;
  *)
    echo "Unknown command: $COMMAND"
    echo "Run $0 without arguments to see usage"
    exit 1
    ;;
esac 