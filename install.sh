#!/bin/bash

# Installation script for Pump Control System
# For Raspberry Pi running Raspbian

# Exit on any error
set -e

# Get current user
CURRENT_USER=$(whoami)
if [ "$CURRENT_USER" = "root" ]; then
    echo "Please run this script as a non-root user with sudo privileges"
    exit 1
fi

echo "Starting Pump Control System installation as user: $CURRENT_USER"

# Update system
echo "Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install required system packages
echo "Installing system dependencies..."
sudo apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    nginx \
    supervisor

# Create application directory
echo "Creating application directory..."
sudo mkdir -p /opt/pump-control
sudo chown -R $CURRENT_USER:$CURRENT_USER /opt/pump-control

# Create virtual environment
echo "Setting up Python virtual environment..."
python3 -m venv /opt/pump-control/venv

# Activate virtual environment
source /opt/pump-control/venv/bin/activate

# Install Python packages
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install \
    flask \
    flask-login \
    flask-sqlalchemy \
    gunicorn \
    requests \
    RPi.GPIO

# Clone the repository
echo "Cloning application repository..."
cd /opt/pump-control
git clone https://github.com/typecookie/PumpControl.git app

# Create necessary directories
echo "Creating required directories..."
mkdir -p /home/$CURRENT_USER/.pump_control
mkdir -p /opt/pump-control/logs

# Setup supervisor configuration
echo "Configuring supervisor..."
sudo tee /etc/supervisor/conf.d/pump-control.conf << EOF
[program:pump-control]
directory=/opt/pump-control/app
command=/opt/pump-control/venv/bin/gunicorn -c gunicorn_config.py 'app:create_app()'
user=$CURRENT_USER
autostart=true
autorestart=true
stderr_logfile=/opt/pump-control/logs/supervisor.err.log
stdout_logfile=/opt/pump-control/logs/supervisor.out.log
environment=PATH="/opt/pump-control/venv/bin"
startsecs=5
stopwaitsecs=10
EOF

# Setup nginx configuration
echo "Configuring nginx..."
sudo tee /etc/nginx/sites-available/pump-control << EOF
server {
    listen 80;
    server_name _;

    access_log /opt/pump-control/logs/nginx-access.log;
    error_log /opt/pump-control/logs/nginx-error.log;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
}
EOF

# Enable the nginx site
sudo ln -sf /etc/nginx/sites-available/pump-control /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Create systemd service for auto-start
echo "Creating systemd service..."
sudo tee /etc/systemd/system/pump-control.service << EOF
[Unit]
Description=Pump Control System
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
Group=$CURRENT_USER
WorkingDirectory=/opt/pump-control/app
Environment="PATH=/opt/pump-control/venv/bin"
ExecStart=/opt/pump-control/venv/bin/gunicorn -c gunicorn_config.py 'app:create_app()'
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Setup permissions
echo "Setting up permissions..."
sudo chown -R $CURRENT_USER:$CURRENT_USER /opt/pump-control
sudo chown -R $CURRENT_USER:$CURRENT_USER /home/$CURRENT_USER/.pump_control

# Create and configure log files
echo "Setting up log files..."
sudo mkdir -p /opt/pump-control/logs
sudo touch /opt/pump-control/logs/supervisor.err.log
sudo touch /opt/pump-control/logs/supervisor.out.log
sudo touch /opt/pump-control/logs/nginx-access.log
sudo touch /opt/pump-control/logs/nginx-error.log
sudo chown -R $CURRENT_USER:$CURRENT_USER /opt/pump-control/logs
sudo chmod 755 /opt/pump-control/logs
sudo chmod 644 /opt/pump-control/logs/*.log

# Add user to gpio group if it exists
if getent group gpio > /dev/null; then
    echo "Adding user to gpio group..."
    sudo usermod -a -G gpio $CURRENT_USER
fi

# Create maintenance scripts
echo "Creating maintenance scripts..."

# Create fix-permissions script
sudo tee /opt/pump-control/fix-permissions.sh << EOF
#!/bin/bash
sudo chown -R $CURRENT_USER:$CURRENT_USER /opt/pump-control/logs
sudo chmod 755 /opt/pump-control/logs
sudo touch /opt/pump-control/logs/supervisor.err.log
sudo touch /opt/pump-control/logs/supervisor.out.log
sudo touch /opt/pump-control/logs/nginx-access.log
sudo touch /opt/pump-control/logs/nginx-error.log
sudo chown $CURRENT_USER:$CURRENT_USER /opt/pump-control/logs/*.log
sudo chmod 644 /opt/pump-control/logs/*.log
EOF
chmod +x /opt/pump-control/fix-permissions.sh

# Create restart script
sudo tee /opt/pump-control/restart.sh << EOF
#!/bin/bash
echo "Stopping services..."
sudo systemctl stop pump-control
sudo systemctl stop nginx
sudo supervisorctl stop all

echo "Fixing permissions..."
/opt/pump-control/fix-permissions.sh

echo "Restarting services..."
sudo systemctl daemon-reload
sudo supervisorctl reread
sudo supervisorctl update
sudo systemctl start nginx
sudo systemctl start pump-control

echo "Service status:"
sudo systemctl status pump-control
EOF
chmod +x /opt/pump-control/restart.sh

# Create uninstall script
echo "Creating uninstall script..."
tee /opt/pump-control/uninstall.sh << EOF
#!/bin/bash
echo "Stopping services..."
sudo systemctl stop pump-control
sudo systemctl stop nginx
sudo supervisorctl stop pump-control

echo "Removing files..."
sudo rm -rf /opt/pump-control
sudo rm -f /etc/supervisor/conf.d/pump-control.conf
sudo rm -f /etc/nginx/sites-available/pump-control
sudo rm -f /etc/nginx/sites-enabled/pump-control
sudo rm -f /etc/systemd/system/pump-control.service
sudo rm -rf /home/$CURRENT_USER/.pump_control

echo "Reloading services..."
sudo systemctl daemon-reload
sudo supervisorctl reread
sudo supervisorctl update

echo "Uninstall complete"
EOF
chmod +x /opt/pump-control/uninstall.sh

# Initial service start
echo "Starting services..."
sudo systemctl daemon-reload
sudo systemctl enable pump-control
sudo systemctl enable nginx

# Stop any running instances
sudo systemctl stop pump-control
sudo systemctl stop nginx
sudo supervisorctl stop all

# Run permission fix
/opt/pump-control/fix-permissions.sh

# Start services
sudo supervisorctl reread
sudo supervisorctl update
sudo systemctl start nginx
sudo systemctl start pump-control

echo "Installation complete!"
echo "The application should now be running on port 80"
echo "Available management scripts:"
echo "- Fix permissions: /opt/pump-control/fix-permissions.sh"
echo "- Restart services: /opt/pump-control/restart.sh"
echo "- Uninstall: /opt/pump-control/uninstall.sh"
echo ""
echo "To check service status:"
echo "sudo systemctl status pump-control"
echo "sudo supervisorctl status"