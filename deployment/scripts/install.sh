#!/bin/bash

# Real Estate CRM - Ubuntu 20.04+ Installation Script
# This script sets up Odoo 16 CE with Real Estate CRM on Ubuntu VPS

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ODOO_USER="odoo"
ODOO_HOME="/opt/odoo"
ODOO_VERSION="16.0"
POSTGRES_VERSION="13"
DOMAIN="crm.yourdomain.com"  # Change this to your domain

echo -e "${GREEN}Starting Real Estate CRM Installation...${NC}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run as root (use sudo)${NC}"
    exit 1
fi

# Update system
echo -e "${YELLOW}Updating system packages...${NC}"
apt update && apt upgrade -y

# Install system dependencies
echo -e "${YELLOW}Installing system dependencies...${NC}"
apt install -y \
    python3-pip \
    python3-dev \
    python3-venv \
    python3-wheel \
    libxml2-dev \
    libxslt1-dev \
    libevent-dev \
    libsasl2-dev \
    libldap2-dev \
    libpq-dev \
    libpng-dev \
    libjpeg-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libwebp-dev \
    libharfbuzz-dev \
    libfribidi-dev \
    libxcb1-dev \
    libssl-dev \
    libffi-dev \
    git \
    curl \
    wget \
    unzip \
    build-essential \
    software-properties-common \
    supervisor \
    nginx \
    certbot \
    python3-certbot-nginx \
    wkhtmltopdf

# Install Node.js (required for some Odoo features)
echo -e "${YELLOW}Installing Node.js...${NC}"
curl -fsSL https://deb.nodesource.com/setup_16.x | bash -
apt install -y nodejs

# Install PostgreSQL
echo -e "${YELLOW}Installing PostgreSQL...${NC}"
apt install -y postgresql postgresql-contrib postgresql-client

# Create PostgreSQL user
echo -e "${YELLOW}Setting up PostgreSQL...${NC}"
sudo -u postgres createuser -s $ODOO_USER 2>/dev/null || true
sudo -u postgres psql -c "ALTER USER $ODOO_USER PASSWORD 'your_secure_password_here';" 2>/dev/null || true

# Create odoo user
echo -e "${YELLOW}Creating Odoo user...${NC}"
adduser --system --quiet --shell=/bin/bash --home=$ODOO_HOME --gecos 'ODOO' --group $ODOO_USER || true

# Create directories
echo -e "${YELLOW}Creating directories...${NC}"
mkdir -p $ODOO_HOME/{custom-addons,config,data,logs,backups,sessions}
mkdir -p /var/log/odoo
mkdir -p /var/log/supervisor

# Set permissions
chown -R $ODOO_USER:$ODOO_USER $ODOO_HOME
chown -R $ODOO_USER:$ODOO_USER /var/log/odoo

# Download Odoo
echo -e "${YELLOW}Downloading Odoo $ODOO_VERSION...${NC}"
cd $ODOO_HOME
if [ ! -d "odoo" ]; then
    git clone --depth 1 --branch $ODOO_VERSION https://github.com/odoo/odoo.git
fi

# Create Python virtual environment
echo -e "${YELLOW}Creating Python virtual environment...${NC}"
sudo -u $ODOO_USER python3 -m venv $ODOO_HOME/venv

# Install Python dependencies
echo -e "${YELLOW}Installing Python dependencies...${NC}"
sudo -u $ODOO_USER $ODOO_HOME/venv/bin/pip install --upgrade pip
sudo -u $ODOO_USER $ODOO_HOME/venv/bin/pip install wheel
sudo -u $ODOO_USER $ODOO_HOME/venv/bin/pip install -r $ODOO_HOME/odoo/requirements.txt

# Install additional Python packages for Real Estate CRM
echo -e "${YELLOW}Installing additional Python packages...${NC}"
sudo -u $ODOO_USER $ODOO_HOME/venv/bin/pip install \
    requests \
    geopy \
    phonenumbers \
    qrcode \
    pillow \
    opencv-python-headless \
    marshmallow \
    redis \
    celery \
    sentry-sdk \
    cerberus

# Copy Real Estate CRM module
echo -e "${YELLOW}Setting up Real Estate CRM module...${NC}"
if [ -d "/tmp/real-estate-crm" ]; then
    cp -r /tmp/real-estate-crm/* $ODOO_HOME/custom-addons/
    chown -R $ODOO_USER:$ODOO_USER $ODOO_HOME/custom-addons
fi

# Copy configuration files
echo -e "${YELLOW}Setting up configuration files...${NC}"
if [ -f "$ODOO_HOME/custom-addons/config/odoo.conf" ]; then
    cp $ODOO_HOME/custom-addons/config/odoo.conf $ODOO_HOME/config/
    chown $ODOO_USER:$ODOO_USER $ODOO_HOME/config/odoo.conf
    
    # Update configuration with actual values
    sed -i "s/your_secure_password_here/$(openssl rand -base64 32)/g" $ODOO_HOME/config/odoo.conf
    sed -i "s/your_admin_password_here/$(openssl rand -base64 32)/g" $ODOO_HOME/config/odoo.conf
    sed -i "s|/opt/odoo/custom-addons|$ODOO_HOME/custom-addons|g" $ODOO_HOME/config/odoo.conf
    sed -i "s|/opt/odoo/data|$ODOO_HOME/data|g" $ODOO_HOME/config/odoo.conf
fi

# Setup supervisor
echo -e "${YELLOW}Setting up Supervisor...${NC}"
if [ -f "$ODOO_HOME/custom-addons/deployment/supervisor/odoo.conf" ]; then
    cp $ODOO_HOME/custom-addons/deployment/supervisor/odoo.conf /etc/supervisor/conf.d/
    sed -i "s|/opt/odoo|$ODOO_HOME|g" /etc/supervisor/conf.d/odoo.conf
fi

# Setup Nginx
echo -e "${YELLOW}Setting up Nginx...${NC}"
if [ -f "$ODOO_HOME/custom-addons/config/nginx/crm.conf" ]; then
    cp $ODOO_HOME/custom-addons/config/nginx/crm.conf /etc/nginx/sites-available/
    sed -i "s/crm.yourdomain.com/$DOMAIN/g" /etc/nginx/sites-available/crm.conf
    
    # Enable site
    ln -sf /etc/nginx/sites-available/crm.conf /etc/nginx/sites-enabled/
    
    # Remove default site
    rm -f /etc/nginx/sites-enabled/default
fi

# Setup firewall
echo -e "${YELLOW}Configuring firewall...${NC}"
ufw allow 22
ufw allow 80
ufw allow 443
ufw --force enable

# Start services
echo -e "${YELLOW}Starting services...${NC}"
systemctl enable postgresql
systemctl start postgresql
systemctl enable supervisor
systemctl start supervisor
systemctl enable nginx

# Reload supervisor
supervisorctl reread
supervisorctl update
supervisorctl start odoo

# Test Nginx configuration
nginx -t && systemctl reload nginx

# Setup SSL certificate
echo -e "${YELLOW}Setting up SSL certificate...${NC}"
certbot --nginx -d $DOMAIN --non-interactive --agree-tos -m admin@$DOMAIN || true

# Setup log rotation
echo -e "${YELLOW}Setting up log rotation...${NC}"
cat > /etc/logrotate.d/odoo << EOF
/var/log/odoo/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 odoo odoo
    postrotate
        supervisorctl restart odoo
    endscript
}
EOF

# Create backup script
echo -e "${YELLOW}Creating backup script...${NC}"
cat > $ODOO_HOME/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/odoo/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="real_estate_crm"

# Create database backup
sudo -u postgres pg_dump $DB_NAME > $BACKUP_DIR/db_backup_$DATE.sql

# Create filestore backup
tar -czf $BACKUP_DIR/filestore_backup_$DATE.tar.gz $ODOO_HOME/data/filestore

# Remove old backups (keep 30 days)
find $BACKUP_DIR -name "*.sql" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
EOF

chmod +x $ODOO_HOME/backup.sh
chown $ODOO_USER:$ODOO_USER $ODOO_HOME/backup.sh

# Add to crontab
(crontab -u $ODOO_USER -l 2>/dev/null; echo "0 2 * * * $ODOO_HOME/backup.sh") | crontab -u $ODOO_USER -

# Create database
echo -e "${YELLOW}Creating database...${NC}"
sudo -u $ODOO_USER $ODOO_HOME/venv/bin/python3 $ODOO_HOME/odoo/odoo-bin \
    -c $ODOO_HOME/config/odoo.conf \
    -d real_estate_crm \
    -i base,real_estate_crm \
    --stop-after-init \
    --without-demo=all

# Final status
echo -e "${GREEN}Installation completed!${NC}"
echo -e "${GREEN}================================${NC}"
echo -e "Odoo Real Estate CRM has been installed successfully!"
echo ""
echo "Access URLs:"
echo "  - Main site: https://$DOMAIN"
echo "  - Database: real_estate_crm"
echo ""
echo "System locations:"
echo "  - Odoo home: $ODOO_HOME"
echo "  - Configuration: $ODOO_HOME/config/odoo.conf"
echo "  - Logs: /var/log/odoo/"
echo "  - Backups: $ODOO_HOME/backups/"
echo ""
echo "Services status:"
supervisorctl status odoo
systemctl status nginx --no-pager -l
systemctl status postgresql --no-pager -l
echo ""
echo -e "${YELLOW}Important: Update passwords in configuration files!${NC}"
echo -e "${YELLOW}Config file: $ODOO_HOME/config/odoo.conf${NC}"
echo ""
echo -e "${GREEN}Installation log: /var/log/install.log${NC}"