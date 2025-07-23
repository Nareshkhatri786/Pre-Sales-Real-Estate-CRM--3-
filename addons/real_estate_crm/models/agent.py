# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class RealEstateAgent(models.Model):
    """Real Estate Agent Model"""
    
    _name = 'real.estate.agent'
    _description = 'Real Estate Agent'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'
    _rec_name = 'name'
    
    # Basic Information
    name = fields.Char(
        string='Agent Name',
        required=True,
        tracking=True,
        help='Full name of the agent'
    )
    
    user_id = fields.Many2one(
        'res.users',
        string='Related User',
        required=True,
        tracking=True,
        help='System user account for this agent'
    )
    
    partner_id = fields.Many2one(
        'res.partner',
        string='Related Contact',
        help='Contact record for this agent'
    )
    
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee Record',
        help='HR employee record if applicable'
    )
    
    # Contact Information
    email = fields.Char(
        string='Email',
        related='user_id.email',
        store=True
    )
    
    phone = fields.Char(
        string='Phone',
        help='Primary phone number'
    )
    
    mobile = fields.Char(
        string='Mobile',
        help='Mobile phone number'
    )
    
    # Professional Information
    license_number = fields.Char(
        string='License Number',
        help='Real estate license number'
    )
    
    license_expiry = fields.Date(
        string='License Expiry',
        help='License expiration date'
    )
    
    specialization = fields.Selection([
        ('residential', 'Residential'),
        ('commercial', 'Commercial'),
        ('industrial', 'Industrial'),
        ('luxury', 'Luxury Properties'),
        ('rental', 'Rental Properties'),
        ('investment', 'Investment Properties'),
    ], string='Specialization', help='Agent specialization area')
    
    languages = fields.Char(
        string='Languages',
        help='Languages spoken by the agent'
    )
    
    # Employment Details
    hire_date = fields.Date(
        string='Hire Date',
        help='Date when agent joined the company'
    )
    
    employment_type = fields.Selection([
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('contractor', 'Contractor'),
        ('freelance', 'Freelance'),
    ], string='Employment Type', default='full_time')
    
    status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('on_leave', 'On Leave'),
        ('terminated', 'Terminated'),
    ], string='Status', default='active', tracking=True)
    
    # Territory and Team
    territory_ids = fields.Many2many(
        'real.estate.territory',
        string='Territories',
        help='Assigned territories'
    )
    
    team_id = fields.Many2one(
        'crm.team',
        string='Sales Team',
        help='Sales team membership'
    )
    
    manager_id = fields.Many2one(
        'real.estate.agent',
        string='Manager',
        help='Direct manager/supervisor'
    )
    
    # Commission Structure
    commission_rate = fields.Float(
        string='Commission Rate (%)',
        default=5.0,
        help='Default commission rate percentage'
    )
    
    commission_structure = fields.Selection([
        ('percentage', 'Percentage of Sale'),
        ('fixed', 'Fixed Amount'),
        ('tiered', 'Tiered Structure'),
    ], string='Commission Structure', default='percentage')
    
    # Performance Metrics
    target_monthly = fields.Monetary(
        string='Monthly Target',
        currency_field='currency_id',
        help='Monthly sales target'
    )
    
    target_yearly = fields.Monetary(
        string='Yearly Target',
        currency_field='currency_id',
        help='Yearly sales target'
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id
    )
    
    # Statistics and Computed Fields
    total_sales = fields.Monetary(
        string='Total Sales',
        currency_field='currency_id',
        compute='_compute_performance_stats',
        store=True
    )
    
    total_listings = fields.Integer(
        string='Total Listings',
        compute='_compute_listing_stats',
        store=True
    )
    
    active_listings = fields.Integer(
        string='Active Listings',
        compute='_compute_listing_stats',
        store=True
    )
    
    closed_deals = fields.Integer(
        string='Closed Deals',
        compute='_compute_performance_stats',
        store=True
    )
    
    leads_count = fields.Integer(
        string='Leads Count',
        compute='_compute_lead_stats'
    )
    
    clients_count = fields.Integer(
        string='Clients Count',
        compute='_compute_client_stats'
    )
    
    appointments_count = fields.Integer(
        string='Appointments Count',
        compute='_compute_appointment_stats'
    )
    
    # Performance Ratings
    performance_rating = fields.Selection([
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('average', 'Average'),
        ('below_average', 'Below Average'),
        ('poor', 'Poor'),
    ], string='Performance Rating', compute='_compute_performance_rating')
    
    # Relations
    property_ids = fields.One2many(
        'real.estate.property',
        'salesperson_id',
        string='Properties'
    )
    
    lead_ids = fields.One2many(
        'real.estate.lead',
        'user_id',
        string='Leads'
    )
    
    appointment_ids = fields.One2many(
        'real.estate.appointment',
        'agent_id',
        string='Appointments'
    )
    
    commission_ids = fields.One2many(
        'real.estate.commission',
        'agent_id',
        string='Commissions'
    )
    
    # Bio and Marketing
    bio = fields.Html(
        string='Biography',
        help='Agent biography for marketing materials'
    )
    
    photo = fields.Image(
        string='Photo',
        max_width=1024,
        max_height=1024,
        help='Agent photo'
    )
    
    achievements = fields.Text(
        string='Achievements',
        help='Notable achievements and awards'
    )
    
    @api.depends('property_ids', 'property_ids.state', 'property_ids.selling_price')
    def _compute_performance_stats(self):
        """Compute performance statistics"""
        for record in self:
            sold_properties = record.property_ids.filtered(lambda p: p.state == 'sold')
            record.closed_deals = len(sold_properties)
            record.total_sales = sum(sold_properties.mapped('selling_price'))
    
    @api.depends('property_ids', 'property_ids.state')
    def _compute_listing_stats(self):
        """Compute listing statistics"""
        for record in self:
            record.total_listings = len(record.property_ids)
            record.active_listings = len(
                record.property_ids.filtered(lambda p: p.state in ['available', 'offer_received'])
            )
    
    @api.depends('lead_ids')
    def _compute_lead_stats(self):
        """Compute lead statistics"""
        for record in self:
            record.leads_count = len(record.lead_ids)
    
    @api.depends('user_id')
    def _compute_client_stats(self):
        """Compute client statistics"""
        for record in self:
            # Count unique clients from leads and properties
            client_ids = set()
            client_ids.update(record.lead_ids.mapped('partner_id').ids)
            client_ids.update(record.property_ids.mapped('buyer_id').ids)
            client_ids.update(record.property_ids.mapped('seller_id').ids)
            client_ids.discard(False)  # Remove False values
            record.clients_count = len(client_ids)
    
    @api.depends('appointment_ids')
    def _compute_appointment_stats(self):
        """Compute appointment statistics"""
        for record in self:
            record.appointments_count = len(record.appointment_ids)
    
    @api.depends('total_sales', 'target_yearly', 'closed_deals')
    def _compute_performance_rating(self):
        """Compute performance rating"""
        for record in self:
            if not record.target_yearly or record.target_yearly == 0:
                record.performance_rating = 'average'
                continue
            
            achievement_ratio = record.total_sales / record.target_yearly
            
            if achievement_ratio >= 1.2:
                record.performance_rating = 'excellent'
            elif achievement_ratio >= 1.0:
                record.performance_rating = 'good'
            elif achievement_ratio >= 0.8:
                record.performance_rating = 'average'
            elif achievement_ratio >= 0.6:
                record.performance_rating = 'below_average'
            else:
                record.performance_rating = 'poor'
    
    @api.constrains('commission_rate')
    def _check_commission_rate(self):
        """Validate commission rate"""
        for record in self:
            if record.commission_rate < 0 or record.commission_rate > 100:
                raise ValidationError(_('Commission rate must be between 0 and 100'))
    
    @api.constrains('license_expiry')
    def _check_license_expiry(self):
        """Check license expiry"""
        for record in self:
            if record.license_expiry and record.license_expiry < fields.Date.today():
                # Create activity for license renewal
                record.activity_schedule(
                    'mail.mail_activity_data_todo',
                    summary='License Renewal Required',
                    note=f'Real estate license for {record.name} has expired on {record.license_expiry}',
                    user_id=record.manager_id.user_id.id if record.manager_id else record.user_id.id
                )
    
    def action_view_properties(self):
        """View agent's properties"""
        self.ensure_one()
        return {
            'name': _('Properties: %s') % self.name,
            'view_mode': 'tree,form',
            'res_model': 'real.estate.property',
            'type': 'ir.actions.act_window',
            'domain': [('salesperson_id', '=', self.user_id.id)],
            'context': {'default_salesperson_id': self.user_id.id},
        }
    
    def action_view_leads(self):
        """View agent's leads"""
        self.ensure_one()
        return {
            'name': _('Leads: %s') % self.name,
            'view_mode': 'tree,form,kanban',
            'res_model': 'real.estate.lead',
            'type': 'ir.actions.act_window',
            'domain': [('user_id', '=', self.user_id.id)],
            'context': {'default_user_id': self.user_id.id},
        }
    
    def action_view_appointments(self):
        """View agent's appointments"""
        self.ensure_one()
        return {
            'name': _('Appointments: %s') % self.name,
            'view_mode': 'tree,form,calendar',
            'res_model': 'real.estate.appointment',
            'type': 'ir.actions.act_window',
            'domain': [('agent_id', '=', self.id)],
            'context': {'default_agent_id': self.id},
        }
    
    def action_view_commissions(self):
        """View agent's commissions"""
        self.ensure_one()
        return {
            'name': _('Commissions: %s') % self.name,
            'view_mode': 'tree,form',
            'res_model': 'real.estate.commission',
            'type': 'ir.actions.act_window',
            'domain': [('agent_id', '=', self.id)],
            'context': {'default_agent_id': self.id},
        }
    
    def get_performance_data(self, period='month'):
        """Get performance data for dashboards"""
        self.ensure_one()
        
        from datetime import datetime, timedelta
        
        if period == 'month':
            start_date = datetime.now().replace(day=1)
        elif period == 'quarter':
            current_month = datetime.now().month
            quarter_start = ((current_month - 1) // 3) * 3 + 1
            start_date = datetime.now().replace(month=quarter_start, day=1)
        else:  # year
            start_date = datetime.now().replace(month=1, day=1)
        
        # Get properties sold in period
        sold_properties = self.property_ids.filtered(
            lambda p: p.state == 'sold' and 
            p.write_date >= start_date
        )
        
        # Get leads created in period
        period_leads = self.lead_ids.filtered(
            lambda l: l.create_date >= start_date
        )
        
        return {
            'sales_amount': sum(sold_properties.mapped('selling_price')),
            'properties_sold': len(sold_properties),
            'leads_generated': len(period_leads),
            'conversion_rate': (len(sold_properties) / len(period_leads) * 100) if period_leads else 0,
        }


class RealEstateTerritory(models.Model):
    """Real Estate Territory Model"""
    
    _name = 'real.estate.territory'
    _description = 'Real Estate Territory'
    _order = 'name'
    
    name = fields.Char(
        string='Territory Name',
        required=True,
        help='Name of the territory'
    )
    
    description = fields.Text(
        string='Description',
        help='Territory description'
    )
    
    # Geographic boundaries
    zip_codes = fields.Text(
        string='ZIP Codes',
        help='Comma-separated list of ZIP codes'
    )
    
    cities = fields.Text(
        string='Cities',
        help='Comma-separated list of cities'
    )
    
    states = fields.Many2many(
        'res.country.state',
        string='States/Provinces'
    )
    
    countries = fields.Many2many(
        'res.country',
        string='Countries'
    )
    
    # Territory management
    manager_id = fields.Many2one(
        'real.estate.agent',
        string='Territory Manager',
        help='Agent responsible for this territory'
    )
    
    agent_ids = fields.Many2many(
        'real.estate.agent',
        'agent_territory_rel',
        'territory_id',
        'agent_id',
        string='Assigned Agents'
    )
    
    active = fields.Boolean(
        string='Active',
        default=True
    )
    
    # Statistics
    property_count = fields.Integer(
        string='Properties in Territory',
        compute='_compute_territory_stats'
    )
    
    agent_count = fields.Integer(
        string='Number of Agents',
        compute='_compute_agent_count'
    )
    
    @api.depends('agent_ids')
    def _compute_agent_count(self):
        """Compute number of assigned agents"""
        for record in self:
            record.agent_count = len(record.agent_ids)
    
    @api.depends('zip_codes', 'cities')
    def _compute_territory_stats(self):
        """Compute territory statistics"""
        for record in self:
            # This would need to be enhanced with actual geographic matching
            record.property_count = 0