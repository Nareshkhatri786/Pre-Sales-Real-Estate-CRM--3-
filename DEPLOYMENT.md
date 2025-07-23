# Real Estate CRM - Deployment Guide

## Quick Start Guide for Ubuntu VPS Deployment

### 1. Prerequisites
- Ubuntu 20.04 or later VPS
- Root access
- Domain name pointing to your server
- At least 4GB RAM, 20GB disk space

### 2. Automated Installation

```bash
# Download and run the installation script
wget https://raw.githubusercontent.com/Nareshkhatri786/Pre-Sales-Real-Estate-CRM--3-/main/deployment/scripts/install.sh
chmod +x install.sh

# Edit the domain configuration
nano install.sh
# Change: DOMAIN="crm.yourdomain.com"

# Run installation
sudo ./install.sh
```

### 3. Manual Installation Steps

#### System Setup
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3-pip python3-dev python3-venv python3-wheel \
    libxml2-dev libxslt1-dev libevent-dev libsasl2-dev libldap2-dev \
    libpq-dev libpng-dev libjpeg-dev libfreetype6-dev liblcms2-dev \
    libwebp-dev libharfbuzz-dev libfribidi-dev libxcb1-dev libssl-dev \
    libffi-dev git curl wget unzip build-essential software-properties-common \
    supervisor nginx certbot python3-certbot-nginx wkhtmltopdf

# Install PostgreSQL
sudo apt install -y postgresql postgresql-contrib postgresql-client

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_16.x | sudo -E bash -
sudo apt install -y nodejs
```

#### User and Directory Setup
```bash
# Create odoo user
sudo adduser --system --quiet --shell=/bin/bash --home=/opt/odoo --gecos 'ODOO' --group odoo

# Create directories
sudo mkdir -p /opt/odoo/{custom-addons,config,data,logs,backups,sessions}
sudo mkdir -p /var/log/odoo
sudo chown -R odoo:odoo /opt/odoo /var/log/odoo
```

#### PostgreSQL Setup
```bash
# Create database user
sudo -u postgres createuser -s odoo
sudo -u postgres psql -c "ALTER USER odoo PASSWORD 'your_secure_password_here';"

# Run setup script
sudo -u postgres psql -f config/postgresql/setup.sql
```

#### Odoo Installation
```bash
# Download Odoo
cd /opt/odoo
sudo -u odoo git clone --depth 1 --branch 16.0 https://github.com/odoo/odoo.git

# Create virtual environment
sudo -u odoo python3 -m venv venv

# Install Python packages
sudo -u odoo venv/bin/pip install --upgrade pip wheel
sudo -u odoo venv/bin/pip install -r odoo/requirements.txt
sudo -u odoo venv/bin/pip install -r requirements.txt
```

#### Configuration
```bash
# Copy configuration files
sudo cp config/odoo.conf /opt/odoo/config/
sudo cp deployment/supervisor/odoo.conf /etc/supervisor/conf.d/
sudo cp config/nginx/crm.conf /etc/nginx/sites-available/

# Enable Nginx site
sudo ln -s /etc/nginx/sites-available/crm.conf /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Update configurations with your settings
sudo nano /opt/odoo/config/odoo.conf  # Update passwords and paths
sudo nano /etc/nginx/sites-available/crm.conf  # Update domain name
```

#### Service Setup
```bash
# Start services
sudo systemctl enable postgresql supervisor nginx
sudo systemctl start postgresql supervisor

# Reload supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start odoo

# Test and start Nginx
sudo nginx -t
sudo systemctl start nginx

# Setup SSL
sudo certbot --nginx -d crm.yourdomain.com
```

### 4. Database Creation

```bash
# Create database with Real Estate CRM module
sudo -u odoo /opt/odoo/venv/bin/python3 /opt/odoo/odoo/odoo-bin \
    -c /opt/odoo/config/odoo.conf \
    -d real_estate_crm \
    -i base,real_estate_crm \
    --stop-after-init \
    --without-demo=all
```

### 5. Security Setup

#### Firewall Configuration
```bash
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw --force enable
```

#### SSL Certificate Auto-renewal
```bash
# Test renewal
sudo certbot renew --dry-run

# Add to crontab
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### 6. Backup Setup

#### Automated Backup Script
```bash
# The installation script creates /opt/odoo/backup.sh
# Manual setup:
sudo -u odoo crontab -e
# Add: 0 2 * * * /opt/odoo/backup.sh
```

#### Manual Backup
```bash
# Database backup
sudo -u postgres pg_dump real_estate_crm > backup_$(date +%Y%m%d).sql

# Filestore backup
sudo tar -czf filestore_backup_$(date +%Y%m%d).tar.gz /opt/odoo/data/filestore
```

### 7. Monitoring and Maintenance

#### Service Status
```bash
# Check all services
sudo supervisorctl status
sudo systemctl status nginx postgresql

# Check logs
sudo tail -f /var/log/odoo/odoo.log
sudo tail -f /var/log/nginx/crm.yourdomain.com.error.log
```

#### Performance Monitoring
```bash
# Monitor resources
htop
df -h
free -h

# Database performance
sudo -u postgres psql real_estate_crm -c "SELECT * FROM pg_stat_activity;"
```

### 8. Troubleshooting

#### Common Issues

**Odoo won't start:**
```bash
sudo supervisorctl status odoo
sudo tail -f /var/log/supervisor/odoo.log
# Check configuration and permissions
```

**Database connection error:**
```bash
sudo systemctl status postgresql
sudo -u postgres psql -l
# Verify database exists and user has access
```

**Nginx configuration error:**
```bash
sudo nginx -t
sudo tail -f /var/log/nginx/error.log
# Check configuration syntax
```

**SSL certificate issues:**
```bash
sudo certbot certificates
sudo certbot renew --dry-run
# Verify domain DNS points to server
```

#### Performance Issues
1. **Increase worker processes** in odoo.conf
2. **Optimize PostgreSQL** configuration
3. **Monitor memory usage** and adjust limits
4. **Check disk space** and clean logs if needed

### 9. Configuration Reference

#### Odoo Configuration (/opt/odoo/config/odoo.conf)
```ini
[options]
# Database
db_host = localhost
db_port = 5432
db_user = odoo
db_password = your_secure_password_here
db_name = real_estate_crm

# Server
http_port = 8069
workers = 4
max_cron_threads = 2
proxy_mode = True

# Paths
addons_path = /opt/odoo/addons,/opt/odoo/custom-addons,/opt/odoo/real-estate-crm/addons
data_dir = /opt/odoo/data
logfile = /var/log/odoo/odoo.log

# Security
admin_passwd = your_admin_password_here
list_db = False

# Performance
limit_memory_hard = 2684354560
limit_memory_soft = 2147483648
limit_request = 8192
limit_time_cpu = 600
limit_time_real = 1200
```

#### Nginx Configuration
```nginx
server {
    listen 443 ssl http2;
    server_name crm.yourdomain.com;
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/crm.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/crm.yourdomain.com/privkey.pem;
    
    # Proxy to Odoo
    location / {
        proxy_pass http://127.0.0.1:8069;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_redirect off;
    }
    
    # Longpolling
    location /longpolling {
        proxy_pass http://127.0.0.1:8072;
    }
}
```

### 10. Maintenance Schedule

#### Daily
- Monitor service status
- Check disk space
- Review error logs

#### Weekly
- Review backup integrity
- Monitor performance metrics
- Check security updates

#### Monthly
- Update system packages
- Review database performance
- Clean old log files
- Test backup restore procedure

### 11. Contact and Support

For issues or support:
- GitHub Issues: https://github.com/Nareshkhatri786/Pre-Sales-Real-Estate-CRM--3-/issues
- Documentation: README.md
- Professional Support: support@realestate-crm.com