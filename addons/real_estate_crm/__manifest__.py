{
    'name': 'Real Estate CRM',
    'version': '16.0.1.0.0',
    'category': 'Sales/CRM',
    'summary': 'Complete Real Estate CRM solution for property management, lead tracking, and client relations',
    'description': """
Real Estate CRM - Comprehensive Solution
========================================

This module provides a complete Real Estate CRM solution including:

**Property Management:**
* Property listings with detailed information
* Property photos and virtual tour integration
* Property categories (residential, commercial, rental, sale)
* Advanced property search and filtering
* Property valuation tracking
* Geographic mapping integration

**Lead Management:**
* Lead capture from multiple sources
* Lead scoring and qualification
* Automated follow-up reminders
* Lead conversion tracking
* Communication history

**Client Management:**
* Buyer and seller profiles
* Client preferences and requirements
* Communication tracking
* Document management
* Contract and agreement tracking

**Agent Management:**
* Agent profiles and territories
* Commission tracking
* Performance metrics
* Team collaboration tools

**Features:**
* Mobile-responsive interface
* Advanced reporting and analytics
* Email and SMS integration
* Document generation
* Calendar integration
* Task management
* Automated workflows

**Technical Features:**
* Odoo 16 CE compatible
* PostgreSQL optimized
* Multi-company support
* RESTful API integration
* Customizable fields and views
    """,
    'author': 'Real Estate CRM Team',
    'website': 'https://github.com/Nareshkhatri786/Pre-Sales-Real-Estate-CRM--3-',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'crm',
        'contacts',
        'sale',
        'website',
        'calendar',
        'document',
        'hr',
        'project',
        'account',
    ],
    'external_dependencies': {
        'python': [
            'requests',
            'geopy',
            'phonenumbers',
            'qrcode',
            'PIL',
        ],
    },
    'data': [
        # Security
        'security/real_estate_security.xml',
        'security/ir.model.access.csv',
        
        # Data
        'data/property_type_data.xml',
        'data/property_status_data.xml',
        'data/email_templates.xml',
        'data/automated_actions.xml',
        
        # Views
        'views/property_views.xml',
        'views/property_type_views.xml',
        'views/client_views.xml',
        'views/lead_views.xml',
        'views/agent_views.xml',
        'views/appointment_views.xml',
        'views/valuation_views.xml',
        'views/contract_views.xml',
        'views/commission_views.xml',
        
        # Menus
        'views/menu_views.xml',
        
        # Reports
        'report/property_report.xml',
        'report/client_report.xml',
        'report/sales_report.xml',
        
        # Wizards
        'wizard/property_search_wizard.xml',
        'wizard/bulk_email_wizard.xml',
        'wizard/commission_calculate_wizard.xml',
    ],
    'demo': [
        'data/demo_property_data.xml',
        'data/demo_client_data.xml',
        'data/demo_lead_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'real_estate_crm/static/src/css/real_estate.css',
            'real_estate_crm/static/src/js/property_map.js',
            'real_estate_crm/static/src/js/image_gallery.js',
        ],
        'web.assets_frontend': [
            'real_estate_crm/static/src/css/frontend.css',
            'real_estate_crm/static/src/js/property_search.js',
        ],
    },
    'images': [
        'static/description/icon.png',
        'static/description/banner.png',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'sequence': 10,
    'price': 0,
    'currency': 'USD',
    'support': 'support@realestate-crm.com',
}