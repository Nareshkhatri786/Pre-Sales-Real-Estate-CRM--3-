# Real Estate CRM - Odoo 16 CE

A comprehensive Real Estate CRM solution built for Odoo 16 Community Edition, designed for seamless deployment on Ubuntu 20.04+ VPS servers with PostgreSQL, Nginx, and Supervisor.

## 🏠 Features

### Core Real Estate Management
- **Property Management**: Complete property lifecycle management with detailed information, photos, documents, and virtual tours
- **Client Management**: Enhanced contact management with buyer/seller profiles, preferences, and communication tracking
- **Lead Management**: Advanced lead tracking with scoring, qualification, and conversion workflows
- **Agent Management**: Agent profiles, territory management, performance tracking, and commission calculations
- **Appointment Scheduling**: Integrated calendar system for property viewings and client meetings
- **Property Valuation**: Professional valuation system with comparables and market analysis
- **Contract Management**: Complete contract lifecycle with milestones and document management
- **Commission Tracking**: Automated commission calculations with splits and deductions

### Technical Features
- **Odoo 16 CE Compatible**: Built with latest Odoo 16 APIs and best practices
- **PostgreSQL Optimized**: Designed for PostgreSQL 13+ with proper indexing and performance tuning
- **Mobile Responsive**: Modern web interface optimized for mobile devices
- **RESTful API Ready**: Controller-based architecture for API integrations
- **Portal Integration**: Client portal for property viewing and appointment management
- **Email Integration**: Automated email templates and communication tracking
- **Geographic Integration**: Map integration with GPS coordinates and location-based search
- **Document Management**: File upload and management with categorization
- **Reporting & Analytics**: Comprehensive reports and dashboard views

## 🚀 Quick Installation

### Prerequisites
- Ubuntu 20.04 or later
- Root or sudo access
- Domain name pointing to your server (e.g., crm.yourdomain.com)

### Automated Installation

1. **Download the installation script:**
   ```bash
   wget https://raw.githubusercontent.com/Nareshkhatri786/Pre-Sales-Real-Estate-CRM--3-/main/deployment/scripts/install.sh
   chmod +x install.sh
   ```

2. **Edit the configuration:**
   ```bash
   nano install.sh
   # Update DOMAIN variable with your domain name
   DOMAIN="crm.yourdomain.com"
   ```

3. **Run the installation:**
   ```bash
   sudo ./install.sh
   ```

The script will automatically:
- Install all system dependencies
- Set up PostgreSQL with optimized configuration
- Install and configure Odoo 16 CE
- Set up Nginx reverse proxy with SSL
- Configure Supervisor for process management
- Create automated backup scripts
- Set up log rotation

### Manual Installation

<details>
<summary>Click to expand manual installation steps</summary>

#### 1. System Dependencies
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-dev python3-venv python3-wheel \
    libxml2-dev libxslt1-dev libevent-dev libsasl2-dev libldap2-dev \
    libpq-dev libpng-dev libjpeg-dev libfreetype6-dev liblcms2-dev \
    libwebp-dev libharfbuzz-dev libfribidi-dev libxcb1-dev libssl-dev \
    libffi-dev git curl wget unzip build-essential software-properties-common \
    supervisor nginx certbot python3-certbot-nginx wkhtmltopdf postgresql \
    postgresql-contrib postgresql-client
```

#### 2. Create Odoo User
```bash
sudo adduser --system --quiet --shell=/bin/bash --home=/opt/odoo --gecos 'ODOO' --group odoo
```

#### 3. PostgreSQL Setup
```bash
sudo -u postgres createuser -s odoo
sudo -u postgres psql -c "ALTER USER odoo PASSWORD 'your_secure_password_here';"
sudo -u postgres psql -f config/postgresql/setup.sql
```

#### 4. Odoo Installation
```bash
sudo mkdir -p /opt/odoo/{custom-addons,config,data,logs,backups,sessions}
cd /opt/odoo
sudo git clone --depth 1 --branch 16.0 https://github.com/odoo/odoo.git
sudo python3 -m venv venv
sudo -u odoo venv/bin/pip install --upgrade pip wheel
sudo -u odoo venv/bin/pip install -r odoo/requirements.txt
sudo -u odoo venv/bin/pip install -r requirements.txt
```

#### 5. Configuration
```bash
sudo cp config/odoo.conf /opt/odoo/config/
sudo cp deployment/supervisor/odoo.conf /etc/supervisor/conf.d/
sudo cp config/nginx/crm.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/crm.conf /etc/nginx/sites-enabled/
```

#### 6. Start Services
```bash
sudo systemctl enable postgresql supervisor nginx
sudo supervisorctl reread && sudo supervisorctl update
sudo supervisorctl start odoo
sudo certbot --nginx -d crm.yourdomain.com
```

</details>

## 📁 Project Structure

```
/
├── addons/real_estate_crm/           # Main CRM module
│   ├── __manifest__.py              # Module manifest
│   ├── models/                      # Business logic models
│   │   ├── property_model.py        # Property management
│   │   ├── client.py                # Client/contact management
│   │   ├── lead.py                  # Lead management
│   │   ├── agent.py                 # Agent management
│   │   ├── appointment.py           # Appointment scheduling
│   │   ├── valuation.py             # Property valuation
│   │   ├── contract.py              # Contract management
│   │   └── commission.py            # Commission tracking
│   ├── views/                       # UI views and templates
│   ├── controllers/                 # Web controllers
│   ├── security/                    # Security rules and access
│   ├── data/                        # Master data and configurations
│   └── static/                      # CSS, JS, images
├── config/                          # Configuration files
│   ├── odoo.conf                    # Odoo server configuration
│   ├── postgresql/setup.sql         # Database setup
│   └── nginx/crm.conf              # Nginx configuration
├── deployment/                      # Deployment scripts
│   ├── scripts/install.sh          # Automated installation
│   └── supervisor/odoo.conf        # Process management
└── requirements.txt                 # Python dependencies
```

## 🔧 Configuration

### Environment Variables
Create `/opt/odoo/config/odoo.conf` with your specific settings:

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
addons_path = /opt/odoo/addons,/opt/odoo/custom-addons,/opt/odoo/real-estate-crm/addons

# Security
admin_passwd = your_admin_password_here
list_db = False
proxy_mode = True
```

### Database Configuration
The system is optimized for PostgreSQL 13+ with the following features:
- Proper indexing for property search
- Full-text search capabilities
- Geographic data support (optional PostGIS)
- Performance tuning for large datasets

### Nginx Configuration
SSL-enabled reverse proxy with:
- HTTP to HTTPS redirect
- Security headers
- Gzip compression
- Static file caching
- WebSocket support for real-time features

## 📊 Usage

### Initial Setup
1. Access your installation at `https://crm.yourdomain.com`
2. Create your database and install the Real Estate CRM module
3. Configure your company information
4. Set up property types and lead stages
5. Create agent profiles
6. Import or create your first properties

### Key Workflows

#### Property Management
1. **Add Properties**: Create property listings with photos, descriptions, and features
2. **Property Valuation**: Conduct professional valuations with comparable analysis
3. **Marketing**: Generate marketing materials and list properties
4. **Inquiries**: Manage incoming leads and inquiries
5. **Offers**: Track and manage property offers
6. **Contracts**: Create and manage sales contracts

#### Lead Management
1. **Lead Capture**: Capture leads from website, phone, referrals
2. **Qualification**: Score and qualify leads based on criteria
3. **Assignment**: Assign leads to appropriate agents
4. **Follow-up**: Schedule and track follow-up activities
5. **Conversion**: Convert qualified leads to opportunities

#### Client Management
1. **Profile Creation**: Create detailed client profiles with preferences
2. **Property Matching**: Automatically match clients with suitable properties
3. **Communication**: Track all client communications
4. **Appointments**: Schedule property viewings and meetings
5. **Relationship Management**: Maintain long-term client relationships

### API Integration
The system provides RESTful endpoints for:
- Property search and filtering
- Lead creation and management
- Appointment scheduling
- Client portal access

## 🛡️ Security

### Access Control
- **Role-based Security**: Three main roles (User, Agent, Manager)
- **Record-level Security**: Agents can only access their own records
- **Portal Access**: Secure client portal for property viewing
- **Data Privacy**: GDPR-compliant data handling

### System Security
- **SSL/TLS Encryption**: All traffic encrypted with Let's Encrypt certificates
- **Firewall Configuration**: Proper UFW firewall setup
- **Database Security**: Secure PostgreSQL configuration
- **Regular Updates**: Automated system updates and security patches

## 📈 Performance

### Optimization Features
- **Database Indexing**: Optimized indexes for fast property search
- **Caching**: Redis caching for improved performance
- **CDN Ready**: Static file optimization for CDN delivery
- **Worker Processes**: Multi-worker configuration for high load
- **Background Jobs**: Celery integration for background processing

### Monitoring
- **Log Management**: Centralized logging with rotation
- **Performance Monitoring**: Built-in performance tracking
- **Error Tracking**: Sentry integration for error monitoring
- **Backup System**: Automated daily backups

## 🔄 Backup & Maintenance

### Automated Backups
Daily backups include:
- Database dump (PostgreSQL)
- File store backup (attachments, images)
- Configuration backup
- 30-day retention policy

### Maintenance Tasks
- **Log Rotation**: Automated log rotation with logrotate
- **Database Maintenance**: Weekly VACUUM and ANALYZE
- **Security Updates**: Automated security updates
- **SSL Renewal**: Automatic Let's Encrypt renewal

## 🐛 Troubleshooting

### Common Issues

#### Service Not Starting
```bash
# Check service status
sudo supervisorctl status odoo
sudo systemctl status nginx postgresql

# Check logs
sudo tail -f /var/log/odoo/odoo.log
sudo tail -f /var/log/nginx/error.log
```

#### Database Connection Issues
```bash
# Test database connection
sudo -u odoo psql -h localhost -d real_estate_crm

# Check PostgreSQL status
sudo systemctl status postgresql
```

#### SSL Certificate Issues
```bash
# Renew SSL certificate
sudo certbot renew --dry-run

# Test Nginx configuration
sudo nginx -t
```

### Performance Issues
1. **Check Worker Processes**: Ensure adequate workers in `odoo.conf`
2. **Database Performance**: Monitor slow queries and optimize indexes
3. **Memory Usage**: Monitor memory consumption and adjust limits
4. **Network**: Check network latency and bandwidth

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the LGPL-3 License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Documentation
- [Odoo 16 Documentation](https://www.odoo.com/documentation/16.0/)
- [Real Estate CRM Wiki](https://github.com/Nareshkhatri786/Pre-Sales-Real-Estate-CRM--3-/wiki)

### Community Support
- [GitHub Issues](https://github.com/Nareshkhatri786/Pre-Sales-Real-Estate-CRM--3-/issues)
- [Discussions](https://github.com/Nareshkhatri786/Pre-Sales-Real-Estate-CRM--3-/discussions)

### Professional Support
For professional support, customization, and deployment services, please contact:
- Email: support@realestate-crm.com
- Website: [Real Estate CRM](https://github.com/Nareshkhatri786/Pre-Sales-Real-Estate-CRM--3-)

---

## 🏗️ System Requirements

### Minimum Requirements
- **OS**: Ubuntu 20.04 LTS or later
- **Memory**: 4GB RAM
- **Storage**: 20GB SSD
- **CPU**: 2 vCPU cores
- **Network**: 100 Mbps connection

### Recommended Requirements
- **OS**: Ubuntu 22.04 LTS
- **Memory**: 8GB RAM
- **Storage**: 50GB SSD
- **CPU**: 4 vCPU cores
- **Network**: 1 Gbps connection

### Software Dependencies
- **Python**: 3.8+
- **PostgreSQL**: 13+
- **Nginx**: 1.18+
- **Supervisor**: 4.0+
- **Odoo**: 16.0 CE

---

**Built with ❤️ for the Real Estate Industry**