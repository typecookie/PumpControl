#!/bin/bash

# PumpControl Installation Script
# Simple script to install the PumpControl system to /opt/pump-control

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
SERVICE_NAME="pump-control"
REPO_URL="https://github.com/typecookie/PumpControl.git"
ACTUAL_USER=$(logname || whoami)
BACKUP_DIR="$INSTALL_DIR/backups"

echo "User: $ACTUAL_USER"

# Install dependencies
echo "Installing dependencies..."
apt-get update
apt-get install -y python3 python3-pip python3-venv git nginx rsync

# Create directories
echo "Creating directories..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$LOG_DIR"
mkdir -p "$BACKUP_DIR"
mkdir -p "/home/$ACTUAL_USER/.pump_control"

# Set permissions
chown -R "$ACTUAL_USER:$ACTUAL_USER" "$INSTALL_DIR"
chown -R "$ACTUAL_USER:$ACTUAL_USER" "/home/$ACTUAL_USER/.pump_control"

# Clone repository
echo "Cloning repository..."
if [ -d "$INSTALL_DIR/.git" ]; then
  echo "Repository exists, backing up and updating..."
  
  # Create backup directory with timestamp
  TIMESTAMP=$(date +"%Y%m%d-%H%M%S")
  BACKUP_PATH="$BACKUP_DIR/pump-control-backup-$TIMESTAMP"
  mkdir -p "$BACKUP_DIR"
  
  # Create backup
  rsync -a --exclude 'venv' --exclude 'logs' --exclude 'backups' --exclude '.git' \
    "$INSTALL_DIR/" "$BACKUP_PATH/"
  
  # Backup venv if it exists
  if [ -d "$INSTALL_DIR/venv" ]; then
    mv "$INSTALL_DIR/venv" "/tmp/pump-control-venv-temp"
  fi
  
  # Clean directory but preserve logs
  mv "$LOG_DIR" "/tmp/pump-control-logs-temp"
  rm -rf "$INSTALL_DIR"/*
  
  # Clone fresh copy to temporary location
  git clone "$REPO_URL" "/tmp/pump-control-git-temp"
  
  # Copy repository files
  cp -r "/tmp/pump-control-git-temp"/* "$INSTALL_DIR/"
  
  # Restore logs and venv
  mkdir -p "$LOG_DIR"
  if [ -d "/tmp/pump-control-logs-temp" ]; then
    cp -r "/tmp/pump-control-logs-temp"/* "$LOG_DIR/"
    rm -rf "/tmp/pump-control-logs-temp"
  fi
  
  if [ -d "/tmp/pump-control-venv-temp" ]; then
    mv "/tmp/pump-control-venv-temp" "$INSTALL_DIR/venv"
  fi
  
  # Cleanup temporary directory
  rm -rf "/tmp/pump-control-git-temp"
else
  echo "Fresh installation..."
  # For a fresh installation, just clone directly
  # First, backup existing content if any
  if [ "$(ls -A $INSTALL_DIR)" ]; then
    TIMESTAMP=$(date +"%Y%m%d-%H%M%S")
    BACKUP_PATH="$BACKUP_DIR/pre-install-$TIMESTAMP"
    mkdir -p "$BACKUP_PATH"
    mv "$INSTALL_DIR"/* "$BACKUP_PATH/" 2>/dev/null || true
  fi
  
  # Clone repository to temp and copy
  git clone "$REPO_URL" "/tmp/pump-control-git-temp"
  cp -r "/tmp/pump-control-git-temp"/* "$INSTALL_DIR/"
  rm -rf "/tmp/pump-control-git-temp"
fi

# Setup Python virtual environment
echo "Setting up Python virtual environment..."
if [ ! -d "$INSTALL_DIR/venv" ]; then
  python3 -m venv "$INSTALL_DIR/venv"
fi

# Install Python dependencies
source "$INSTALL_DIR/venv/bin/activate"
pip install --upgrade pip
if [ -f "$INSTALL_DIR/requirements.txt" ]; then
  pip install -r "$INSTALL_DIR/requirements.txt"
else
  echo "requirements.txt not found, installing core dependencies..."
  pip install flask flask-login flask-sqlalchemy gunicorn requests
  
  # Install RPi.GPIO if on a Raspberry Pi
  if grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
    pip install RPi.GPIO
  fi
fi
deactivate

# Configure nginx
echo "Configuring nginx..."
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

# Enable site
ln -sf /etc/nginx/sites-available/pump-control /etc/nginx/sites-enabled/

# Remove default site if it exists
if [ -f /etc/nginx/sites-enabled/default ]; then
  rm /etc/nginx/sites-enabled/default
fi

# Configure systemd service
echo "Configuring systemd service..."
cat > /etc/systemd/system/pump-control.service << EOF
[Unit]
Description=Pump Control System
After=network.target

[Service]
Type=simple
User=${ACTUAL_USER}
Group=${ACTUAL_USER}
WorkingDirectory=${INSTALL_DIR}
Environment="PATH=${INSTALL_DIR}/venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONPATH=${INSTALL_DIR}"
Environment="FLASK_APP=app"
Environment="FLASK_ENV=production"
ExecStart=${INSTALL_DIR}/venv/bin/gunicorn --config ${INSTALL_DIR}/gunicorn_config.py 'app:create_app()'
Restart=always
RestartSec=5
StandardOutput=append:${LOG_DIR}/gunicorn.log
StandardError=append:${LOG_DIR}/gunicorn.err

[Install]
WantedBy=multi-user.target
EOF

# Setup log files
echo "Setting up log files..."
touch "$LOG_DIR/nginx-access.log"
touch "$LOG_DIR/nginx-error.log"
touch "$LOG_DIR/gunicorn.log"
touch "$LOG_DIR/gunicorn.err"
touch "$LOG_DIR/error.log"

# Set permissions
chmod 755 "$LOG_DIR"
chmod 644 "$LOG_DIR"/*.log
chown -R "$ACTUAL_USER:$ACTUAL_USER" "$LOG_DIR"
chown -R "$ACTUAL_USER:$ACTUAL_USER" "$INSTALL_DIR"

# Create helper scripts
echo "Creating helper scripts..."

# Fix permissions script
cat > "$INSTALL_DIR/fix-permissions.sh" << EOF
#!/bin/bash
sudo chown -R ${ACTUAL_USER}:${ACTUAL_USER} ${INSTALL_DIR}
sudo chmod 755 ${LOG_DIR}
sudo chmod 644 ${LOG_DIR}/*.log
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
git pull

echo "Updating dependencies..."
source ${INSTALL_DIR}/venv/bin/activate
pip install -r requirements.txt
deactivate

echo "Restarting service..."
sudo systemctl restart pump-control
echo "Update complete!"
EOF
chmod +x "$INSTALL_DIR/update.sh"

# Set ownership for scripts
chown "$ACTUAL_USER:$ACTUAL_USER" "$INSTALL_DIR"/*.sh

# Add user to gpio group if we're on a Raspberry Pi
if grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
  if getent group gpio > /dev/null; then
    echo "Adding user to gpio group..."
    usermod -a -G gpio "$ACTUAL_USER"
  fi
fi

# Enable and start services
echo "Enabling and starting services..."
systemctl daemon-reload
systemctl enable pump-control
systemctl restart nginx
systemctl restart pump-control || echo "Note: pump-control service failed to start. This may be normal if configuration is incomplete."

echo ""
echo "==================================================="
echo "PumpControl installation complete!"
echo ""
echo "Installation directory: $INSTALL_DIR"
echo ""
echo "Available management scripts:"
echo "- Fix permissions: $INSTALL_DIR/fix-permissions.sh"
echo "- Restart services: $INSTALL_DIR/restart.sh"
echo "- Update application: $INSTALL_DIR/update.sh"
echo ""
echo "To check service status: sudo systemctl status pump-control"
echo "==================================================="