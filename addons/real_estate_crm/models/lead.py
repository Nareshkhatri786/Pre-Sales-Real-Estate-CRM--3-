# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class RealEstateLead(models.Model):
    """Real Estate Lead Model - extends CRM functionality"""
    
    _name = 'real.estate.lead'
    _description = 'Real Estate Lead'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'priority desc, create_date desc'
    _rec_name = 'name'
    
    # Basic Information
    name = fields.Char(
        string='Subject',
        required=True,
        tracking=True,
        help='Lead subject or description'
    )
    
    reference = fields.Char(
        string='Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
        help='Unique lead reference number'
    )
    
    partner_id = fields.Many2one(
        'res.partner',
        string='Contact',
        tracking=True,
        help='Related contact/client'
    )
    
    partner_name = fields.Char(
        string='Contact Name',
        help='Contact name if partner not created yet'
    )
    
    email_from = fields.Char(
        string='Email',
        help='Contact email address'
    )
    
    phone = fields.Char(
        string='Phone',
        help='Contact phone number'
    )
    
    mobile = fields.Char(
        string='Mobile',
        help='Contact mobile number'
    )
    
    # Lead Classification
    lead_type = fields.Selection([
        ('buyer', 'Buyer Lead'),
        ('seller', 'Seller Lead'),
        ('rental_seeker', 'Rental Seeker'),
        ('landlord', 'Landlord'),
        ('investor', 'Investor'),
    ], string='Lead Type', required=True, default='buyer', tracking=True)
    
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Very High'),
    ], string='Priority', default='1', tracking=True)
    
    # Lead Source
    source_id = fields.Many2one(
        'utm.source',
        string='Source',
        help='Lead source (Website, Advertisement, etc.)'
    )
    
    medium_id = fields.Many2one(
        'utm.medium',
        string='Medium',
        help='Lead medium (Email, Social Media, etc.)'
    )
    
    campaign_id = fields.Many2one(
        'utm.campaign',
        string='Campaign',
        help='Marketing campaign'
    )
    
    # Property Interest
    interested_property_id = fields.Many2one(
        'real.estate.property',
        string='Interested Property',
        help='Specific property of interest'
    )
    
    property_types = fields.Many2many(
        'real.estate.property.type',
        'lead_property_type_rel',
        'lead_id',
        'property_type_id',
        string='Interested Property Types'
    )
    
    # Budget and Requirements
    budget_min = fields.Monetary(
        string='Minimum Budget',
        currency_field='currency_id',
        help='Minimum budget for property'
    )
    
    budget_max = fields.Monetary(
        string='Maximum Budget',
        currency_field='currency_id',
        help='Maximum budget for property'
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id
    )
    
    # Property Requirements
    preferred_locations = fields.Text(
        string='Preferred Locations',
        help='Preferred areas or locations'
    )
    
    min_bedrooms = fields.Integer(
        string='Minimum Bedrooms',
        default=0
    )
    
    max_bedrooms = fields.Integer(
        string='Maximum Bedrooms',
        default=0
    )
    
    min_bathrooms = fields.Integer(
        string='Minimum Bathrooms',
        default=0
    )
    
    garage_required = fields.Boolean(
        string='Garage Required',
        default=False
    )
    
    garden_required = fields.Boolean(
        string='Garden Required',
        default=False
    )
    
    # Lead Management
    stage_id = fields.Many2one(
        'real.estate.lead.stage',
        string='Stage',
        required=True,
        tracking=True,
        group_expand='_read_group_stage_ids',
        default=lambda self: self._get_default_stage()
    )
    
    user_id = fields.Many2one(
        'res.users',
        string='Salesperson',
        default=lambda self: self.env.user,
        tracking=True,
        help='Assigned salesperson'
    )
    
    team_id = fields.Many2one(
        'crm.team',
        string='Sales Team',
        help='Sales team handling this lead'
    )
    
    # Dates
    date_open = fields.Datetime(
        string='Assigned Date',
        readonly=True,
        help='Date when lead was assigned'
    )
    
    date_closed = fields.Datetime(
        string='Closed Date',
        readonly=True,
        help='Date when lead was closed'
    )
    
    date_last_stage_update = fields.Datetime(
        string='Last Stage Update',
        default=fields.Datetime.now,
        help='Last time stage was updated'
    )
    
    expected_closing = fields.Date(
        string='Expected Closing',
        help='Expected date for lead closure'
    )
    
    # Communication
    description = fields.Html(
        string='Notes',
        help='Additional notes and information'
    )
    
    # Lead Scoring
    lead_score = fields.Float(
        string='Lead Score',
        compute='_compute_lead_score',
        store=True,
        help='Automatically calculated lead quality score'
    )
    
    lead_temperature = fields.Selection([
        ('cold', 'Cold'),
        ('warm', 'Warm'),
        ('hot', 'Hot'),
    ], string='Temperature', compute='_compute_lead_temperature', store=True)
    
    # Statistics
    days_to_assign = fields.Integer(
        string='Days to Assign',
        compute='_compute_days_to_assign',
        help='Days between creation and assignment'
    )
    
    days_to_close = fields.Integer(
        string='Days to Close',
        compute='_compute_days_to_close',
        help='Days between creation and closure'
    )
    
    # Relations
    appointment_ids = fields.One2many(
        'real.estate.appointment',
        'lead_id',
        string='Appointments'
    )
    
    activity_count = fields.Integer(
        string='Activities',
        compute='_compute_activity_count'
    )
    
    appointment_count = fields.Integer(
        string='Appointments',
        compute='_compute_appointment_count'
    )
    
    # Conversion
    is_converted = fields.Boolean(
        string='Converted',
        default=False,
        help='Whether lead has been converted to opportunity'
    )
    
    converted_opportunity_id = fields.Many2one(
        'crm.lead',
        string='Converted Opportunity',
        help='CRM opportunity created from this lead'
    )
    
    @api.model
    def _get_default_stage(self):
        """Get default stage for new leads"""
        return self.env['real.estate.lead.stage'].search([('sequence', '=', 1)], limit=1)
    
    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        """Stage group expansion for kanban view"""
        return stages.search([], order=order)
    
    @api.depends(
        'budget_min', 'budget_max', 'partner_id', 'phone', 'mobile',
        'email_from', 'interested_property_id', 'source_id'
    )
    def _compute_lead_score(self):
        """Compute lead quality score"""
        for record in self:
            score = 0
            
            # Contact completeness
            if record.partner_id:
                score += 20
            elif record.partner_name:
                score += 10
            
            if record.email_from:
                score += 15
            if record.phone or record.mobile:
                score += 15
            
            # Budget information
            if record.budget_min and record.budget_max:
                score += 20
            elif record.budget_min or record.budget_max:
                score += 10
            
            # Property interest
            if record.interested_property_id:
                score += 15
            elif record.property_types:
                score += 10
            
            # Source quality
            if record.source_id:
                score += 10
            
            # Requirements specificity
            if record.preferred_locations:
                score += 5
            if record.min_bedrooms or record.max_bedrooms:
                score += 5
            
            record.lead_score = min(100, score)  # Cap at 100
    
    @api.depends('lead_score')
    def _compute_lead_temperature(self):
        """Compute lead temperature based on score"""
        for record in self:
            if record.lead_score >= 70:
                record.lead_temperature = 'hot'
            elif record.lead_score >= 40:
                record.lead_temperature = 'warm'
            else:
                record.lead_temperature = 'cold'
    
    @api.depends('create_date', 'date_open')
    def _compute_days_to_assign(self):
        """Compute days between creation and assignment"""
        for record in self:
            if record.create_date and record.date_open:
                delta = record.date_open - record.create_date
                record.days_to_assign = delta.days
            else:
                record.days_to_assign = 0
    
    @api.depends('create_date', 'date_closed')
    def _compute_days_to_close(self):
        """Compute days between creation and closure"""
        for record in self:
            if record.create_date and record.date_closed:
                delta = record.date_closed - record.create_date
                record.days_to_close = delta.days
            else:
                record.days_to_close = 0
    
    @api.depends('activity_ids')
    def _compute_activity_count(self):
        """Compute number of activities"""
        for record in self:
            record.activity_count = len(record.activity_ids)
    
    @api.depends('appointment_ids')
    def _compute_appointment_count(self):
        """Compute number of appointments"""
        for record in self:
            record.appointment_count = len(record.appointment_ids)
    
    @api.model
    def create(self, vals):
        """Override create to generate sequence"""
        if vals.get('reference', _('New')) == _('New'):
            vals['reference'] = self.env['ir.sequence'].next_by_code('real.estate.lead') or _('New')
        return super().create(vals)
    
    def write(self, vals):
        """Override write to track stage changes"""
        if 'stage_id' in vals:
            vals['date_last_stage_update'] = fields.Datetime.now()
            
            # Check if moving to closed stage
            stage = self.env['real.estate.lead.stage'].browse(vals['stage_id'])
            if stage.is_won or stage.is_lost:
                vals['date_closed'] = fields.Datetime.now()
        
        return super().write(vals)
    
    @api.constrains('budget_min', 'budget_max')
    def _check_budget_range(self):
        """Validate budget range"""
        for record in self:
            if record.budget_min and record.budget_max:
                if record.budget_min > record.budget_max:
                    raise ValidationError(_('Minimum budget cannot be greater than maximum budget'))
    
    @api.constrains('min_bedrooms', 'max_bedrooms')
    def _check_bedroom_range(self):
        """Validate bedroom range"""
        for record in self:
            if record.min_bedrooms and record.max_bedrooms:
                if record.min_bedrooms > record.max_bedrooms:
                    raise ValidationError(_('Minimum bedrooms cannot be greater than maximum bedrooms'))
    
    def action_convert_to_opportunity(self):
        """Convert lead to CRM opportunity"""
        self.ensure_one()
        
        # Create opportunity
        opportunity_vals = {
            'name': self.name,
            'partner_id': self.partner_id.id if self.partner_id else False,
            'email_from': self.email_from,
            'phone': self.phone,
            'mobile': self.mobile,
            'user_id': self.user_id.id,
            'team_id': self.team_id.id if self.team_id else False,
            'source_id': self.source_id.id if self.source_id else False,
            'medium_id': self.medium_id.id if self.medium_id else False,
            'campaign_id': self.campaign_id.id if self.campaign_id else False,
            'description': self.description,
            'expected_revenue': self.budget_max or 0,
        }
        
        opportunity = self.env['crm.lead'].create(opportunity_vals)
        
        # Update lead
        self.write({
            'is_converted': True,
            'converted_opportunity_id': opportunity.id,
        })
        
        # Move to converted stage
        converted_stage = self.env['real.estate.lead.stage'].search([('is_won', '=', True)], limit=1)
        if converted_stage:
            self.stage_id = converted_stage
        
        return {
            'name': _('Converted Opportunity'),
            'view_mode': 'form',
            'res_model': 'crm.lead',
            'res_id': opportunity.id,
            'type': 'ir.actions.act_window',
        }
    
    def action_schedule_appointment(self):
        """Schedule appointment with lead"""
        self.ensure_one()
        return {
            'name': _('Schedule Appointment'),
            'view_mode': 'form',
            'res_model': 'real.estate.appointment',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_lead_id': self.id,
                'default_client_id': self.partner_id.id if self.partner_id else False,
                'default_agent_id': self.user_id.id,
                'default_name': f'Appointment for {self.name}',
            },
        }
    
    def action_create_contact(self):
        """Create contact from lead"""
        self.ensure_one()
        
        if self.partner_id:
            raise ValidationError(_('Contact already exists for this lead'))
        
        partner_vals = {
            'name': self.partner_name or 'Contact',
            'email': self.email_from,
            'phone': self.phone,
            'mobile': self.mobile,
            'is_real_estate_client': True,
            'client_type': self.lead_type if self.lead_type != 'rental_seeker' else 'buyer',
            'budget_min': self.budget_min,
            'budget_max': self.budget_max,
            'preferred_property_types': [(6, 0, self.property_types.ids)],
            'preferred_locations': self.preferred_locations,
            'min_bedrooms': self.min_bedrooms,
            'max_bedrooms': self.max_bedrooms,
            'min_bathrooms': self.min_bathrooms,
            'garage_required': self.garage_required,
            'garden_required': self.garden_required,
        }
        
        partner = self.env['res.partner'].create(partner_vals)
        self.partner_id = partner
        
        return {
            'name': _('Contact Created'),
            'view_mode': 'form',
            'res_model': 'res.partner',
            'res_id': partner.id,
            'type': 'ir.actions.act_window',
        }
    
    def get_matching_properties(self):
        """Get properties matching lead requirements"""
        self.ensure_one()
        
        domain = [('state', '=', 'available')]
        
        # Budget filter
        if self.budget_min:
            domain.append(('expected_price', '>=', self.budget_min))
        if self.budget_max:
            domain.append(('expected_price', '<=', self.budget_max))
        
        # Property type filter
        if self.property_types:
            domain.append(('property_type_id', 'in', self.property_types.ids))
        
        # Bedroom filter
        if self.min_bedrooms:
            domain.append(('bedrooms', '>=', self.min_bedrooms))
        if self.max_bedrooms:
            domain.append(('bedrooms', '<=', self.max_bedrooms))
        
        # Bathroom filter
        if self.min_bathrooms:
            domain.append(('bathrooms', '>=', self.min_bathrooms))
        
        # Feature filters
        if self.garage_required:
            domain.append(('garage', '=', True))
        if self.garden_required:
            domain.append(('garden_area', '>', 0))
        
        return self.env['real.estate.property'].search(domain)
    
    def action_view_matching_properties(self):
        """View properties matching lead requirements"""
        self.ensure_one()
        matching_properties = self.get_matching_properties()
        
        return {
            'name': _('Matching Properties for %s') % self.name,
            'view_mode': 'tree,form',
            'res_model': 'real.estate.property',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', matching_properties.ids)],
        }


class RealEstateLeadStage(models.Model):
    """Lead Stages for Real Estate CRM"""
    
    _name = 'real.estate.lead.stage'
    _description = 'Real Estate Lead Stage'
    _order = 'sequence, name'
    
    name = fields.Char(
        string='Stage Name',
        required=True,
        help='Name of the lead stage'
    )
    
    description = fields.Text(
        string='Description',
        help='Description of the stage'
    )
    
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Sequence for ordering stages'
    )
    
    active = fields.Boolean(
        string='Active',
        default=True
    )
    
    fold = fields.Boolean(
        string='Folded in Kanban',
        default=False,
        help='Fold this stage in kanban view'
    )
    
    is_won = fields.Boolean(
        string='Won Stage',
        default=False,
        help='Mark as won/converted stage'
    )
    
    is_lost = fields.Boolean(
        string='Lost Stage',
        default=False,
        help='Mark as lost stage'
    )
    
    # Automation
    requirements = fields.Text(
        string='Requirements',
        help='Requirements to reach this stage'
    )
  
    # Statistics
    lead_count = fields.Integer(
        string='Lead Count',
        compute='_compute_lead_count'
    )
    
    @api.depends()
    def _compute_lead_count(self):
        """Compute number of leads in this stage"""
        for record in self:
            record.lead_count = self.env['real.estate.lead'].search_count([
                ('stage_id', '=', record.id)
            ])