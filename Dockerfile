FROM ubuntu:22.04

# Install necessary packages
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    openssh-client \
    sshpass \
    iputils-ping \
    dnsutils \
    net-tools \
    tcpdump \
    telnet \
    netcat \
    curl \
    wget \
    nmap \
    traceroute \
    iptables \
    iproute2 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN useradd -m -s /bin/bash executor

# Set up working directory
WORKDIR /app

# Copy application files
COPY src /app/src
COPY requirements.txt /app/

# Install Python dependencies
RUN pip3 install -r requirements.txt

# Set up SSH configuration for the user
RUN mkdir -p /home/executor/.ssh && \
    chmod 700 /home/executor/.ssh && \
    chown -R executor:executor /home/executor/.ssh

# Create allowed directories
RUN mkdir -p /tmp/safe && \
    chown -R executor:executor /tmp/safe

# Create secrets directory for SSH credentials
RUN mkdir -p /app/secrets/keys && \
    chmod 700 /app/secrets && \
    chmod 700 /app/secrets/keys && \
    chown -R executor:executor /app/secrets

# Switch to non-root user
USER executor

# Set environment variables
ENV ALLOWED_HOSTS="localhost,127.0.0.1"
ENV ALLOWED_DIRECTORIES="/tmp/safe,/app/secrets"
ENV ALLOWED_REMOTE_COMMANDS="ls,cat,grep,head,tail,df,du,uname,ps,top,ping,ssh,nslookup,dig,tcpdump,telnet"

# Command to start the service
CMD ["python3", "src/itmcp/executor.py"] 