# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class RealEstatePropertyType(models.Model):
    """Property Type Model - Houses, Apartments, Commercial, etc."""
    
    _name = 'real.estate.property.type'
    _description = 'Real Estate Property Type'
    _order = 'name'
    
    name = fields.Char(
        string='Property Type',
        required=True,
        help='Name of the property type (e.g., House, Apartment, Commercial)'
    )
    
    description = fields.Text(
        string='Description',
        help='Detailed description of the property type'
    )
    
    active = fields.Boolean(
        string='Active',
        default=True,
        help='Whether this property type is active'
    )
    
    # Category classification
    category = fields.Selection([
        ('residential', 'Residential'),
        ('commercial', 'Commercial'),
        ('industrial', 'Industrial'),
        ('land', 'Land'),
        ('mixed_use', 'Mixed Use'),
    ], string='Category', required=True, default='residential')
    
    # Transaction types allowed
    for_sale = fields.Boolean(
        string='For Sale',
        default=True,
        help='Can be sold'
    )
    
    for_rent = fields.Boolean(
        string='For Rent',
        default=False,
        help='Can be rented'
    )
    
    # Default values for properties of this type
    default_bedrooms = fields.Integer(
        string='Default Bedrooms',
        default=0,
        help='Default number of bedrooms for this property type'
    )
    
    default_bathrooms = fields.Integer(
        string='Default Bathrooms',
        default=0,
        help='Default number of bathrooms for this property type'
    )
    
    # Sequence for ordering
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Sequence for ordering property types'
    )
    
    # Icon or image
    icon = fields.Binary(
        string='Icon',
        help='Icon for the property type'
    )
    
    # Color for UI
    color = fields.Integer(
        string='Color',
        default=0,
        help='Color index for UI display'
    )
    
    # Relations
    property_ids = fields.One2many(
        'real.estate.property',
        'property_type_id',
        string='Properties'
    )
    
    # Statistics
    property_count = fields.Integer(
        string='Property Count',
        compute='_compute_property_count',
        help='Number of properties of this type'
    )
    
    available_properties = fields.Integer(
        string='Available Properties',
        compute='_compute_available_properties',
        help='Number of available properties of this type'
    )
    
    avg_price = fields.Monetary(
        string='Average Price',
        currency_field='currency_id',
        compute='_compute_avg_price',
        help='Average price for this property type'
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id
    )
    
    @api.depends('property_ids')
    def _compute_property_count(self):
        """Compute total number of properties"""
        for record in self:
            record.property_count = len(record.property_ids)
    
    @api.depends('property_ids.state')
    def _compute_available_properties(self):
        """Compute number of available properties"""
        for record in self:
            record.available_properties = len(
                record.property_ids.filtered(lambda p: p.state == 'available')
            )
    
    @api.depends('property_ids.expected_price')
    def _compute_avg_price(self):
        """Compute average price for this property type"""
        for record in self:
            if record.property_ids:
                prices = record.property_ids.mapped('expected_price')
                record.avg_price = sum(prices) / len(prices) if prices else 0
            else:
                record.avg_price = 0
    
    @api.constrains('name')
    def _check_name_uniqueness(self):
        """Ensure property type names are unique"""
        for record in self:
            if self.search_count([('name', '=ilike', record.name), ('id', '!=', record.id)]) > 0:
                raise ValidationError(_('Property type name must be unique!'))
    
    def action_view_properties(self):
        """Action to view all properties of this type"""
        self.ensure_one()
        return {
            'name': _('Properties: %s') % self.name,
            'view_mode': 'tree,form',
            'res_model': 'real.estate.property',
            'type': 'ir.actions.act_window',
            'domain': [('property_type_id', '=', self.id)],
            'context': {'default_property_type_id': self.id},
        }
    
    def action_view_available_properties(self):
        """Action to view available properties of this type"""
        self.ensure_one()
        return {
            'name': _('Available Properties: %s') % self.name,
            'view_mode': 'tree,form',
            'res_model': 'real.estate.property',
            'type': 'ir.actions.act_window',
            'domain': [
                ('property_type_id', '=', self.id),
                ('state', '=', 'available')
            ],
            'context': {'default_property_type_id': self.id},
        }