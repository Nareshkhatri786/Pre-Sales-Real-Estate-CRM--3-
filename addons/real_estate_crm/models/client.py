# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    """Extend res.partner for Real Estate CRM clients"""
    
    _inherit = 'res.partner'
    
    # Real Estate specific fields
    is_real_estate_client = fields.Boolean(
        string='Is Real Estate Client',
        default=False,
        help='Mark as real estate client'
    )
    
    client_type = fields.Selection([
        ('buyer', 'Buyer'),
        ('seller', 'Seller'),
        ('landlord', 'Landlord'),
        ('tenant', 'Tenant'),
        ('investor', 'Investor'),
        ('agent', 'Agent'),
    ], string='Client Type', help='Type of real estate client')
    
    # Property preferences for buyers
    budget_min = fields.Monetary(
        string='Minimum Budget',
        currency_field='currency_id',
        help='Minimum budget for property purchase/rent'
    )
    
    budget_max = fields.Monetary(
        string='Maximum Budget',
        currency_field='currency_id',
        help='Maximum budget for property purchase/rent'
    )
    
    preferred_property_types = fields.Many2many(
        'real.estate.property.type',
        'partner_property_type_rel',
        'partner_id',
        'property_type_id',
        string='Preferred Property Types'
    )
    
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
    
    # Financial information
    financing_pre_approved = fields.Boolean(
        string='Financing Pre-approved',
        default=False
    )
    
    financing_amount = fields.Monetary(
        string='Pre-approved Amount',
        currency_field='currency_id'
    )
    
    financing_bank = fields.Char(
        string='Financing Bank'
    )
    
    # Credit and identity verification
    credit_check_done = fields.Boolean(
        string='Credit Check Done',
        default=False
    )
    
    credit_score = fields.Integer(
        string='Credit Score'
    )
    
    identity_verified = fields.Boolean(
        string='Identity Verified',
        default=False
    )
    
    # Communication preferences
    preferred_contact_method = fields.Selection([
        ('phone', 'Phone'),
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('whatsapp', 'WhatsApp'),
    ], string='Preferred Contact Method', default='email')
    
    best_contact_time = fields.Selection([
        ('morning', 'Morning (8AM-12PM)'),
        ('afternoon', 'Afternoon (12PM-6PM)'),
        ('evening', 'Evening (6PM-10PM)'),
        ('anytime', 'Any Time'),
    ], string='Best Contact Time', default='anytime')
    
    # Relations
    owned_properties = fields.One2many(
        'real.estate.property',
        'seller_id',
        string='Owned Properties'
    )
    
    purchased_properties = fields.One2many(
        'real.estate.property',
        'buyer_id',
        string='Purchased Properties'
    )
    
    property_leads = fields.One2many(
        'real.estate.lead',
        'partner_id',
        string='Property Leads'
    )
    
    appointments = fields.One2many(
        'real.estate.appointment',
        'client_id',
        string='Appointments'
    )
    
    property_offers = fields.One2many(
        'real.estate.property.offer',
        'partner_id',
        string='Property Offers'
    )
    
    # Statistics and computed fields
    total_properties_owned = fields.Integer(
        string='Total Properties Owned',
        compute='_compute_property_stats'
    )
    
    total_properties_purchased = fields.Integer(
        string='Total Properties Purchased',
        compute='_compute_property_stats'
    )
    
    total_offers_made = fields.Integer(
        string='Total Offers Made',
        compute='_compute_property_stats'
    )
    
    active_leads_count = fields.Integer(
        string='Active Leads',
        compute='_compute_lead_stats'
    )
    
    last_activity_date = fields.Datetime(
        string='Last Activity',
        compute='_compute_last_activity'
    )
    
    # Client scoring
    client_score = fields.Float(
        string='Client Score',
        compute='_compute_client_score',
        help='Automatically calculated client quality score'
    )
    
    client_rating = fields.Selection([
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('average', 'Average'),
        ('poor', 'Poor'),
    ], string='Client Rating', compute='_compute_client_rating')
    
    @api.depends('owned_properties', 'purchased_properties', 'property_offers')
    def _compute_property_stats(self):
        """Compute property-related statistics"""
        for record in self:
            record.total_properties_owned = len(record.owned_properties)
            record.total_properties_purchased = len(record.purchased_properties)
            record.total_offers_made = len(record.property_offers)
    
    @api.depends('property_leads')
    def _compute_lead_stats(self):
        """Compute lead statistics"""
        for record in self:
            record.active_leads_count = len(
                record.property_leads.filtered(lambda l: l.stage_id.name not in ['Won', 'Lost'])
            )
    
    @api.depends('message_ids', 'appointments', 'property_offers')
    def _compute_last_activity(self):
        """Compute last activity date"""
        for record in self:
            dates = []
            if record.message_ids:
                dates.extend(record.message_ids.mapped('date'))
            if record.appointments:
                dates.extend(record.appointments.mapped('write_date'))
            if record.property_offers:
                dates.extend(record.property_offers.mapped('write_date'))
            
            record.last_activity_date = max(dates) if dates else False
    
    @api.depends(
        'total_properties_owned', 'total_properties_purchased',
        'total_offers_made', 'financing_pre_approved',
        'credit_check_done', 'identity_verified'
    )
    def _compute_client_score(self):
        """Compute client quality score"""
        for record in self:
            score = 0
            
            # Property activity score
            score += record.total_properties_owned * 10
            score += record.total_properties_purchased * 15
            score += record.total_offers_made * 5
            
            # Verification bonuses
            if record.financing_pre_approved:
                score += 20
            if record.credit_check_done:
                score += 15
            if record.identity_verified:
                score += 10
            
            # Budget reasonableness
            if record.budget_min and record.budget_max:
                if record.budget_max > record.budget_min:
                    score += 10
            
            record.client_score = min(100, score)  # Cap at 100
    
    @api.depends('client_score')
    def _compute_client_rating(self):
        """Compute client rating based on score"""
        for record in self:
            if record.client_score >= 80:
                record.client_rating = 'excellent'
            elif record.client_score >= 60:
                record.client_rating = 'good'
            elif record.client_score >= 40:
                record.client_rating = 'average'
            else:
                record.client_rating = 'poor'
    
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
    
    def action_view_properties(self):
        """View all properties related to this client"""
        self.ensure_one()
        properties = self.owned_properties | self.purchased_properties
        return {
            'name': _('Properties: %s') % self.name,
            'view_mode': 'tree,form',
            'res_model': 'real.estate.property',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', properties.ids)],
        }
    
    def action_view_leads(self):
        """View all leads for this client"""
        self.ensure_one()
        return {
            'name': _('Leads: %s') % self.name,
            'view_mode': 'tree,form',
            'res_model': 'real.estate.lead',
            'type': 'ir.actions.act_window',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id},
        }
    
    def action_view_appointments(self):
        """View all appointments for this client"""
        self.ensure_one()
        return {
            'name': _('Appointments: %s') % self.name,
            'view_mode': 'tree,form,calendar',
            'res_model': 'real.estate.appointment',
            'type': 'ir.actions.act_window',
            'domain': [('client_id', '=', self.id)],
            'context': {'default_client_id': self.id},
        }
    
    def action_schedule_appointment(self):
        """Schedule new appointment with client"""
        self.ensure_one()
        return {
            'name': _('Schedule Appointment'),
            'view_mode': 'form',
            'res_model': 'real.estate.appointment',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_client_id': self.id,
                'default_agent_id': self.env.user.id,
            },
        }
    
    def action_create_lead(self):
        """Create new lead for client"""
        self.ensure_one()
        return {
            'name': _('Create Lead'),
            'view_mode': 'form',
            'res_model': 'real.estate.lead',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_partner_id': self.id,
                'default_user_id': self.env.user.id,
            },
        }
    
    def get_matching_properties(self):
        """Get properties matching client preferences"""
        self.ensure_one()
        
        domain = [('state', '=', 'available')]
        
        # Budget filter
        if self.budget_min:
            domain.append(('expected_price', '>=', self.budget_min))
        if self.budget_max:
            domain.append(('expected_price', '<=', self.budget_max))
        
        # Property type filter
        if self.preferred_property_types:
            domain.append(('property_type_id', 'in', self.preferred_property_types.ids))
        
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
        """View properties matching client preferences"""
        self.ensure_one()
        matching_properties = self.get_matching_properties()
        
        return {
            'name': _('Matching Properties for %s') % self.name,
            'view_mode': 'tree,form',
            'res_model': 'real.estate.property',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', matching_properties.ids)],
        }
    
    def send_matching_properties_email(self):
        """Send email with matching properties to client"""
        self.ensure_one()
        matching_properties = self.get_matching_properties()
        
        if not matching_properties:
            return False
        
        template = self.env.ref('real_estate_crm.email_template_matching_properties', False)
        if template:
            template.with_context(matching_properties=matching_properties).send_mail(self.id)
        
        return True