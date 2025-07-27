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

# Function to perform common setup tasks
setup_environment() {
    echo "Setting up environment..."
    
    # Create necessary directories
    sudo mkdir -p /opt/pump-control/{logs,venv}
    sudo mkdir -p /home/$CURRENT_USER/.pump_control
    
    # Set correct ownership
    sudo chown -R $CURRENT_USER:$CURRENT_USER /opt/pump-control
    sudo chown -R $CURRENT_USER:$CURRENT_USER /home/$CURRENT_USER/.pump_control
    
    # Setup Python virtual environment if it doesn't exist
    if [ ! -f "/opt/pump-control/venv/bin/activate" ]; then
        echo "Creating new virtual environment..."
        python3 -m venv /opt/pump-control/venv
    fi
    
    # Activate virtual environment
    source /opt/pump-control/venv/bin/activate
    
    # Update pip and install requirements
    pip install --upgrade pip
    pip install \
        flask \
        flask-login \
        flask-sqlalchemy \
        gunicorn \
        requests \
        RPi.GPIO
}

# Function to configure nginx
setup_nginx() {
    echo "Configuring nginx..."
    
    # Create nginx configuration
    sudo tee /etc/nginx/sites-available/pump-control << EOF
server {
    listen 80;
    server_name _;

    access_log /opt/pump-control/logs/nginx-access.log;
    error_log /opt/pump-control/logs/nginx-error.log;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location /static/ {
        alias /opt/pump-control/app/static/;
    }
}
EOF

    # Enable site and remove default
    sudo ln -sf /etc/nginx/sites-available/pump-control /etc/nginx/sites-enabled/
    sudo rm -f /etc/nginx/sites-enabled/default
}

# Function to setup systemd service
setup_systemd() {
    echo "Setting up systemd service..."
    
    sudo tee /etc/systemd/system/pump-control.service << EOF
[Unit]
Description=Pump Control System
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
Group=$CURRENT_USER
WorkingDirectory=/opt/pump-control/app
Environment="PATH=/opt/pump-control/venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONPATH=/opt/pump-control/app"
Environment="FLASK_APP=app"
Environment="FLASK_ENV=production"
ExecStart=/opt/pump-control/venv/bin/gunicorn --config /opt/pump-control/app/gunicorn_config.py 'app:create_app()'
Restart=on-failure
RestartSec=5
StandardOutput=append:/opt/pump-control/logs/gunicorn.log
StandardError=append:/opt/pump-control/logs/gunicorn.err

[Install]
WantedBy=multi-user.target
EOF
}

# Function to setup log files
setup_logs() {
    echo "Setting up log files..."
    
    # Create log files
    sudo touch /opt/pump-control/logs/{nginx-access,nginx-error,gunicorn,error}.log
    
    # Set permissions
    sudo chown -R $CURRENT_USER:$CURRENT_USER /opt/pump-control/logs
    sudo chmod 755 /opt/pump-control/logs
    sudo chmod 644 /opt/pump-control/logs/*.log
}

# Function to create maintenance scripts
create_maintenance_scripts() {
    echo "Creating maintenance scripts..."
    
    # Create fix-permissions script
    sudo tee /opt/pump-control/fix-permissions.sh << EOF
#!/bin/bash
sudo chown -R $CURRENT_USER:$CURRENT_USER /opt/pump-control
sudo chmod 755 /opt/pump-control/logs
sudo chmod 644 /opt/pump-control/logs/*.log
EOF
    sudo chmod +x /opt/pump-control/fix-permissions.sh

    # Create restart script
    sudo tee /opt/pump-control/restart.sh << EOF
#!/bin/bash
echo "Restarting services..."
sudo systemctl restart nginx pump-control
echo "Service status:"
sudo systemctl status pump-control
EOF
    sudo chmod +x /opt/pump-control/restart.sh

    # Create update script
    sudo tee /opt/pump-control/update.sh << EOF
#!/bin/bash
cd /opt/pump-control/app
git pull
source /opt/pump-control/venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart pump-control
echo "Update complete"
EOF
    sudo chmod +x /opt/pump-control/update.sh
}

# Main installation function
install() {
    echo "Starting Pump Control System installation as user: $CURRENT_USER"
    
    # Update system and install dependencies
    echo "Updating system and installing dependencies..."
    sudo apt-get update
    sudo apt-get upgrade -y
    sudo apt-get install -y python3 python3-pip python3-venv git nginx
    
    # Copy current directory contents to installation directory
    echo "Installing application files..."
    sudo mkdir /opt/pump-control
    sudo cp -r . /opt/pump-control/app
    
    # Run setup functions
    setup_environment
    setup_nginx
    setup_systemd
    setup_logs
    create_maintenance_scripts
    
    # Add user to gpio group if it exists
    if getent group gpio > /dev/null; then
        echo "Adding user to gpio group..."
        sudo usermod -a -G gpio $CURRENT_USER
    fi
    
    # Enable and start services
    echo "Starting services..."
    sudo systemctl daemon-reload
    sudo systemctl enable pump-control nginx
    sudo systemctl restart nginx pump-control
    
    echo "Installation complete!"
    echo "Available management scripts:"
    echo "- Fix permissions: /opt/pump-control/fix-permissions.sh"
    echo "- Restart services: /opt/pump-control/restart.sh"
    echo "- Update application: /opt/pump-control/update.sh"
    echo ""
    echo "To check service status: sudo systemctl status pump-control"
}

# Check if this is an update
if [ -d "/opt/pump-control" ]; then
    echo "Existing installation detected. Updating..."
    setup_environment
    sudo cp -r . /opt/pump-control/app
    sudo systemctl restart pump-control
    echo "Update complete!"
else
    install
fi