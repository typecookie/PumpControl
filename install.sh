#!/bin/bash

# PumpControl Installation Script with Dedicated User
# This script creates a dedicated pump-control user and ensures proper permissions

# Exit on any error
set -e

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run this script with sudo or as root"
  exit 1
fi

# Configuration variables
INSTALL_DIR="/opt/pump-control"
LOG_DIR="$INSTALL_DIR/logs"
CONFIG_DIR="/etc/pump-control"
DATA_DIR="/var/lib/pump-control"
BACKUP_DIR="$DATA_DIR/backups"
SERVICE_USER="pump-control"
SERVICE_GROUP="pump-control"
REPO_URL="https://github.com/typecookie/PumpControl.git"
VENV_DIR="$INSTALL_DIR/venv"

echo "===== PumpControl Installation Script ====="
echo "Installation directory: $INSTALL_DIR"
echo "Repository URL: $REPO_URL"
echo "Service user: $SERVICE_USER"

# Function to print section headers
section() {
  echo
  echo "===== $1 ====="
}

# Install dependencies
section "Installing dependencies"
apt-get update
apt-get install -y python3 python3-pip python3-venv git nginx rsync

# Create dedicated user if it doesn't exist
section "Creating dedicated user"
if ! id "$SERVICE_USER" &>/dev/null; then
  useradd -r -m -d "/home/$SERVICE_USER" -s /bin/bash "$SERVICE_USER"
  echo "Created user $SERVICE_USER"
else
  echo "User $SERVICE_USER already exists"
fi

# Create groups if needed and add user to required groups
for group in gpio dialout; do
  if getent group $group &>/dev/null; then
    if ! id -nG "$SERVICE_USER" | grep -qw "$group"; then
      usermod -a -G $group "$SERVICE_USER"
      echo "Added $SERVICE_USER to $group group"
    fi
  fi
done

# Create essential directories
section "Creating directories"
mkdir -p "$INSTALL_DIR"
mkdir -p "$LOG_DIR"
mkdir -p "$CONFIG_DIR"
mkdir -p "$DATA_DIR"
mkdir -p "$BACKUP_DIR"
mkdir -p "/home/$SERVICE_USER/.pump_control"

# Create a clean virtual environment
section "Creating Python virtual environment"
if [ -d "$VENV_DIR" ]; then
  rm -rf "$VENV_DIR"
fi
python3 -m venv "$VENV_DIR"

# Clone or update repository
section "Setting up repository"
if [ -d "$INSTALL_DIR/.git" ]; then
  echo "Repository exists, backing up and updating..."
  
  # Create backup
  TIMESTAMP=$(date +"%Y%m%d-%H%M%S")
  BACKUP_PATH="$BACKUP_DIR/pump-control-backup-$TIMESTAMP"
  mkdir -p "$BACKUP_DIR"
  
  # Backup existing code (excluding venv, logs, etc.)
  rsync -a --exclude 'venv' --exclude 'logs' --exclude '.git' \
    "$INSTALL_DIR/" "$BACKUP_PATH/"
  
  # Clean directory (preserve backups and logs)
  find "$INSTALL_DIR" -mindepth 1 \
    -not -path "$INSTALL_DIR/logs*" \
    -not -path "$INSTALL_DIR/venv*" \
    -exec rm -rf {} \; 2>/dev/null || true
  
  # Clone fresh copy to temporary location
  git clone "$REPO_URL" "/tmp/pump-control-git-temp"
  
  # Copy repository files
  cp -r "/tmp/pump-control-git-temp/"* "$INSTALL_DIR/" 2>/dev/null || true
  
  # Cleanup temporary directory
  rm -rf "/tmp/pump-control-git-temp"
else
  echo "Fresh installation..."
  # Clone repository to temp and copy
  git clone "$REPO_URL" "/tmp/pump-control-git-temp"
  cp -r "/tmp/pump-control-git-temp/"* "$INSTALL_DIR/" 2>/dev/null || true
  rm -rf "/tmp/pump-control-git-temp"
fi

# Install Python dependencies
section "Installing Python dependencies"
$VENV_DIR/bin/pip install --upgrade pip
if [ -f "$INSTALL_DIR/requirements.txt" ]; then
  $VENV_DIR/bin/pip install -r "$INSTALL_DIR/requirements.txt"
else
  echo "requirements.txt not found, installing core dependencies..."
  $VENV_DIR/bin/pip install flask flask-login flask-sqlalchemy gunicorn requests
  
  # Install RPi.GPIO if on a Raspberry Pi
  if [ -e "/proc/device-tree/model" ] && grep -q "Raspberry Pi" /proc/device-tree/model; then
    $VENV_DIR/bin/pip install RPi.GPIO
    echo "Installed RPi.GPIO for Raspberry Pi"
  fi
fi

# Configure GPIO access if we're on a Raspberry Pi
if [ -e "/dev/gpiomem" ]; then
  echo "GPIO device found, setting permissions..."
  chmod 660 /dev/gpiomem
  
  # Set group ownership based on what's available
  if getent group gpio &>/dev/null; then
    chgrp gpio /dev/gpiomem
    echo "Set /dev/gpiomem ownership to root:gpio"
  elif getent group dialout &>/dev/null; then
    chgrp dialout /dev/gpiomem
    echo "Set /dev/gpiomem ownership to root:dialout"
  fi
fi

# Configure default configuration files
section "Setting up configuration"

# Create pump_config.json if it doesn't exist
if [ ! -f "/home/$SERVICE_USER/.pump_control/pump_config.json" ]; then
  cat > "/home/$SERVICE_USER/.pump_control/pump_config.json" << EOF
{
  "pins": {
    "well_pump": 17,
    "dist_pump": 18,
    "winter_high": 26,
    "winter_low": 27,
    "summer_high": 22,
    "summer_low": 23,
    "summer_empty": 24
  },
  "winter_low_timeout": 300,
  "well_pump_flow_rate": 40.0,
  "dist_pump_flow_rate": 15.0,
  "stats_history_max": 1000
}
EOF
  echo "Created default pump configuration"
fi

# Create gpio_config.json if it doesn't exist
if [ ! -f "/home/$SERVICE_USER/.pump_control/gpio_config.json" ]; then
  cat > "/home/$SERVICE_USER/.pump_control/gpio_config.json" << EOF
{
  "reverse_well_pump": false,
  "invert_well_output": false,
  "tank_state": {
    "summer": "unknown",
    "winter": "unknown"
  },
  "invert_sensors": false
}
EOF
  echo "Created default GPIO configuration"
fi

# Configure nginx
section "Configuring nginx"
cat > /etc/nginx/sites-available/pump-control << EOF
server {
    listen 80;
    server_name _;

    proxy_connect_timeout 75s;
    proxy_read_timeout 300s;

    access_log ${LOG_DIR}/nginx-access.log;
    error_log ${LOG_DIR}/nginx-error.log;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_buffering off;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location /static/ {
        root ${INSTALL_DIR}/app/;
        add_header Cache-Control "public, no-transform";
    }
}
EOF

# Enable site and remove default if it exists
ln -sf /etc/nginx/sites-available/pump-control /etc/nginx/sites-enabled/
if [ -f /etc/nginx/sites-enabled/default ]; then
  rm /etc/nginx/sites-enabled/default
fi

# Configure systemd service
section "Configuring systemd service"
cat > /etc/systemd/system/pump-control.service << EOF
[Unit]
Description=Pump Control System
After=network.target

[Service]
Type=simple
User=${SERVICE_USER}
Group=${SERVICE_USER}
WorkingDirectory=${INSTALL_DIR}
Environment="PATH=${VENV_DIR}/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONPATH=${INSTALL_DIR}"
Environment="FLASK_APP=app"
Environment="FLASK_ENV=production"
# Pre-execution steps to ensure proper permissions
ExecStartPre=/bin/bash -c 'for i in /dev/gpiomem /dev/mem /dev/i2c-*; do [ -e \$i ] && chmod 660 \$i && chgrp gpio \$i || true; done'
# Main executable
ExecStart=${VENV_DIR}/bin/gunicorn --config ${INSTALL_DIR}/gunicorn_config.py 'app:create_app()'
Restart=always
RestartSec=5
StandardOutput=append:${LOG_DIR}/gunicorn.log
StandardError=append:${LOG_DIR}/gunicorn.err

[Install]
WantedBy=multi-user.target
EOF

# Setup log files
section "Setting up log files"
touch "$LOG_DIR/nginx-access.log"
touch "$LOG_DIR/nginx-error.log"
touch "$LOG_DIR/gunicorn.log"
touch "$LOG_DIR/gunicorn.err"
touch "$LOG_DIR/error.log"

# Create helper scripts
section "Creating helper scripts"

# Fix permissions script
cat > "$INSTALL_DIR/fix-permissions.sh" << EOF
#!/bin/bash
# Script to fix permissions for PumpControl
sudo chown -R ${SERVICE_USER}:${SERVICE_USER} ${INSTALL_DIR}
sudo chown -R ${SERVICE_USER}:${SERVICE_USER} /home/${SERVICE_USER}/.pump_control
sudo chmod 755 ${LOG_DIR}
sudo chmod 644 ${LOG_DIR}/*.log
sudo chmod +x ${VENV_DIR}/bin/*
echo "Permissions fixed!"
EOF
chmod +x "$INSTALL_DIR/fix-permissions.sh"

# Restart script
cat > "$INSTALL_DIR/restart.sh" << EOF
#!/bin/bash
echo "Restarting services..."
sudo systemctl restart nginx pump-control
echo "Service status:"
sudo systemctl status pump-control --no-pager
EOF
chmod +x "$INSTALL_DIR/restart.sh"

# Update script
cat > "$INSTALL_DIR/update.sh" << EOF
#!/bin/bash
cd ${INSTALL_DIR}
echo "Creating backup..."
TIMESTAMP=\$(date +"%Y%m%d-%H%M%S")
BACKUP_PATH="${BACKUP_DIR}/pump-control-backup-\$TIMESTAMP"
mkdir -p "${BACKUP_DIR}"
rsync -a --exclude 'venv' --exclude 'logs' --exclude 'backups' --exclude '.git' "${INSTALL_DIR}/" "\$BACKUP_PATH/"

echo "Updating repository..."
sudo -u ${SERVICE_USER} git pull

echo "Updating dependencies..."
${VENV_DIR}/bin/pip install --upgrade -r requirements.txt

echo "Restarting service..."
sudo systemctl restart pump-control
echo "Update complete!"
EOF
chmod +x "$INSTALL_DIR/update.sh"

# Test script to verify GPIO access
cat > "$INSTALL_DIR/test-gpio.py" << EOF
#!/usr/bin/env python3
"""
Simple script to test GPIO functionality
"""
import os
import time

try:
    import RPi.GPIO as GPIO
    print("RPi.GPIO module loaded successfully")
    GPIO_AVAILABLE = True
except ImportError:
    print("Failed to load RPi.GPIO - not a Raspberry Pi or module not installed")
    GPIO_AVAILABLE = False

# Test GPIO access if available
if GPIO_AVAILABLE:
    try:
        # Use BCM pin numbering
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # Test pin - modify as needed based on your config
        TEST_PIN = 17  # Well pump pin (default)
        
        # Try to load actual pin from config
        config_path = os.path.expanduser("~/.pump_control/pump_config.json")
        if os.path.exists(config_path):
            import json
            with open(config_path, 'r') as f:
                config = json.load(f)
                if 'pins' in config and 'well_pump' in config['pins']:
                    TEST_PIN = config['pins']['well_pump']
                    print(f"Loaded well pump pin from config: {TEST_PIN}")
        
        print(f"Testing GPIO pin {TEST_PIN}...")
        
        # Set up pin as output
        GPIO.setup(TEST_PIN, GPIO.OUT)
        
        # Turn on
        print("Setting pin HIGH")
        GPIO.output(TEST_PIN, GPIO.HIGH)
        time.sleep(1)
        
        # Read back state
        state = GPIO.input(TEST_PIN)
        print(f"Pin state: {'HIGH' if state else 'LOW'}")
        
        # Turn off
        print("Setting pin LOW")
        GPIO.output(TEST_PIN, GPIO.LOW)
        time.sleep(1)
        
        # Clean up
        GPIO.cleanup()
        print("GPIO test successful")
    except Exception as e:
        print(f"GPIO test failed: {e}")
        if 'Permission' in str(e):
            print("This appears to be a permissions issue with GPIO access")
else:
    print("Skipping GPIO test as RPi.GPIO is not available")
EOF
chmod +x "$INSTALL_DIR/test-gpio.py"

# Set correct permissions for all files and directories
section "Setting final permissions"

# Fix ownership
chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
chown -R "$SERVICE_USER:$SERVICE_USER" "$DATA_DIR"
chown -R "$SERVICE_USER:$SERVICE_USER" "/home/$SERVICE_USER/.pump_control"

# Fix directory permissions
find "$INSTALL_DIR" -type d -exec chmod 755 {} \;
find "$DATA_DIR" -type d -exec chmod 755 {} \;

# Fix file permissions
find "$INSTALL_DIR" -type f -name "*.py" -exec chmod 644 {} \;
find "$INSTALL_DIR" -type f -name "*.sh" -exec chmod 755 {} \;
find "$VENV_DIR/bin" -type f -exec chmod 755 {} \;

# Make sure log directory is accessible and writeable
chmod 755 "$LOG_DIR"
chmod 644 "$LOG_DIR"/*.log
chown -R "$SERVICE_USER:$SERVICE_USER" "$LOG_DIR"

# Make gunicorn and python executable
chmod 755 "$VENV_DIR/bin/gunicorn"
chmod 755 "$VENV_DIR/bin/python"
chmod 755 "$VENV_DIR/bin/python3"
chmod 755 "$VENV_DIR/bin/pip"

# Enable and start services
section "Starting services"
systemctl daemon-reload
systemctl enable pump-control
systemctl restart nginx
systemctl restart pump-control || echo "Warning: pump-control service failed to start. Check the logs for details."

# Display summary
section "Installation complete!"
echo "Installation directory: $INSTALL_DIR"
echo "Service user: $SERVICE_USER"
echo "Configuration directory: /home/$SERVICE_USER/.pump_control"
echo "Log directory: $LOG_DIR"
echo
echo "Available management scripts:"
echo "- Fix permissions: $INSTALL_DIR/fix-permissions.sh"
echo "- Restart services: $INSTALL_DIR/restart.sh"
echo "- Update application: $INSTALL_DIR/update.sh"
echo "- Test GPIO: $INSTALL_DIR/test-gpio.py"
echo
echo "To check service status:"
echo "  sudo systemctl status pump-control"
echo
echo "To view logs:"
echo "  sudo journalctl -u pump-control -f"
echo
echo "==================================================="

# Final service status check
echo "Current service status:"
systemctl status pump-control --no-pager || true