# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
import logging
import base64

_logger = logging.getLogger(__name__)


class RealEstateProperty(models.Model):
    """Real Estate Property Model - Odoo 16 Compatible"""
    
    _name = 'real.estate.property'
    _description = 'Real Estate Property'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    _rec_name = 'name'
    
    # Basic Information
    name = fields.Char(
        string='Property Title',
        required=True,
        tracking=True,
        help='Property listing title'
    )
    
    reference = fields.Char(
        string='Property Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
        help='Unique property reference number'
    )
    
    property_type_id = fields.Many2one(
        'real.estate.property.type',
        string='Property Type',
        required=True,
        tracking=True,
        help='Type of property (House, Apartment, Commercial, etc.)'
    )
    
    # Property Details
    description = fields.Html(
        string='Description',
        help='Detailed property description'
    )
    
    bedrooms = fields.Integer(
        string='Bedrooms',
        default=1,
        help='Number of bedrooms'
    )
    
    bathrooms = fields.Integer(
        string='Bathrooms',
        default=1,
        help='Number of bathrooms'
    )
    
    living_area = fields.Float(
        string='Living Area (sqm)',
        help='Living area in square meters'
    )
    
    total_area = fields.Float(
        string='Total Area (sqm)',
        help='Total area in square meters'
    )
    
    garden_area = fields.Float(
        string='Garden Area (sqm)',
        help='Garden area in square meters'
    )
    
    garage = fields.Boolean(
        string='Garage Available',
        default=False
    )
    
    garage_spaces = fields.Integer(
        string='Garage Spaces',
        help='Number of garage spaces'
    )
    
    # Pricing Information
    expected_price = fields.Monetary(
        string='Expected Price',
        currency_field='currency_id',
        required=True,
        tracking=True,
        help='Expected selling/rental price'
    )
    
    selling_price = fields.Monetary(
        string='Selling Price',
        currency_field='currency_id',
        tracking=True,
        help='Final selling price'
    )
    
    best_price = fields.Monetary(
        string='Best Offer',
        currency_field='currency_id',
        compute='_compute_best_price',
        store=True,
        help='Best offer received'
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.company.currency_id,
        help='Currency for pricing'
    )
    
    # Location Details
    street = fields.Char(string='Street')
    street2 = fields.Char(string='Street 2')
    city = fields.Char(string='City', required=True)
    state_id = fields.Many2one(
        'res.country.state',
        string='State',
        domain="[('country_id', '=?', country_id)]"
    )
    zip_code = fields.Char(string='ZIP Code')
    country_id = fields.Many2one(
        'res.country',
        string='Country',
        required=True
    )
    
    latitude = fields.Float(
        string='Latitude',
        digits=(16, 5),
        help='GPS Latitude coordinate'
    )
    
    longitude = fields.Float(
        string='Longitude',
        digits=(16, 5),
        help='GPS Longitude coordinate'
    )
    
    # Status and Availability
    state = fields.Selection([
        ('draft', 'Draft'),
        ('available', 'Available'),
        ('offer_received', 'Offer Received'),
        ('offer_accepted', 'Offer Accepted'),
        ('sold', 'Sold'),
        ('rented', 'Rented'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', required=True, tracking=True)
    
    availability_date = fields.Date(
        string='Available From',
        default=fields.Date.today,
        help='Date when property becomes available'
    )
    
    # Relationships
    salesperson_id = fields.Many2one(
        'res.users',
        string='Salesperson',
        default=lambda self: self.env.user,
        tracking=True
    )
    
    buyer_id = fields.Many2one(
        'res.partner',
        string='Buyer',
        copy=False,
        tracking=True,
        help='Property buyer'
    )
    
    seller_id = fields.Many2one(
        'res.partner',
        string='Seller',
        required=True,
        tracking=True,
        help='Property seller/owner'
    )
    
    # Property Features
    property_features = fields.Many2many(
        'real.estate.property.feature',
        string='Features',
        help='Property features and amenities'
    )
    
    # Images and Documents
    image_1920 = fields.Image(
        string='Main Image',
        max_width=1920,
        max_height=1920,
        help='Main property image'
    )
    
    image_medium = fields.Image(
        string='Medium Image',
        related='image_1920',
        max_width=128,
        max_height=128,
        store=True
    )
    
    image_small = fields.Image(
        string='Small Image',
        related='image_1920',
        max_width=64,
        max_height=64,
        store=True
    )
    
    property_images = fields.One2many(
        'real.estate.property.image',
        'property_id',
        string='Property Images'
    )
    
    property_documents = fields.One2many(
        'real.estate.property.document',
        'property_id',
        string='Documents'
    )
    
    # Computed Fields
    total_area_display = fields.Char(
        string='Total Area',
        compute='_compute_total_area_display',
        help='Formatted total area display'
    )
    
    full_address = fields.Char(
        string='Address',
        compute='_compute_full_address',
        store=True,
        help='Complete property address'
    )
    
    days_on_market = fields.Integer(
        string='Days on Market',
        compute='_compute_days_on_market',
        help='Number of days property has been on market'
    )
    
    # Relations
    offer_ids = fields.One2many(
        'real.estate.property.offer',
        'property_id',
        string='Offers'
    )
    
    appointment_ids = fields.One2many(
        'real.estate.appointment',
        'property_id',
        string='Appointments'
    )
    
    # Constraints
    @api.constrains('expected_price')
    def _check_expected_price(self):
        """Validate expected price is positive"""
        for record in self:
            if record.expected_price <= 0:
                raise ValidationError(_('Expected price must be positive'))
    
    @api.constrains('bedrooms', 'bathrooms')
    def _check_rooms(self):
        """Validate room numbers are positive"""
        for record in self:
            if record.bedrooms < 0 or record.bathrooms < 0:
                raise ValidationError(_('Number of rooms cannot be negative'))
    
    @api.constrains('living_area', 'total_area')
    def _check_areas(self):
        """Validate areas are positive and logical"""
        for record in self:
            if record.living_area < 0 or record.total_area < 0:
                raise ValidationError(_('Areas cannot be negative'))
            if record.living_area > record.total_area:
                raise ValidationError(_('Living area cannot be greater than total area'))
    
    # Computed Methods
    @api.depends('offer_ids.price')
    def _compute_best_price(self):
        """Compute the best offer price"""
        for record in self:
            if record.offer_ids:
                record.best_price = max(record.offer_ids.mapped('price'))
            else:
                record.best_price = 0
    
    @api.depends('total_area')
    def _compute_total_area_display(self):
        """Format total area for display"""
        for record in self:
            if record.total_area:
                record.total_area_display = f"{record.total_area:.2f} sqm"
            else:
                record.total_area_display = ""
    
    @api.depends('street', 'street2', 'city', 'state_id', 'zip_code', 'country_id')
    def _compute_full_address(self):
        """Compute full formatted address"""
        for record in self:
            address_parts = []
            if record.street:
                address_parts.append(record.street)
            if record.street2:
                address_parts.append(record.street2)
            if record.city:
                address_parts.append(record.city)
            if record.state_id:
                address_parts.append(record.state_id.name)
            if record.zip_code:
                address_parts.append(record.zip_code)
            if record.country_id:
                address_parts.append(record.country_id.name)
            
            record.full_address = ', '.join(address_parts)
    
    @api.depends('create_date', 'state')
    def _compute_days_on_market(self):
        """Calculate days on market"""
        for record in self:
            if record.create_date and record.state in ['available', 'offer_received', 'offer_accepted']:
                delta = datetime.now() - record.create_date
                record.days_on_market = delta.days
            else:
                record.days_on_market = 0
    
    # CRUD Methods
    @api.model
    def create(self, vals):
        """Override create to generate sequence"""
        if vals.get('reference', _('New')) == _('New'):
            vals['reference'] = self.env['ir.sequence'].next_by_code('real.estate.property') or _('New')
        return super().create(vals)
    
    def write(self, vals):
        """Override write to track state changes"""
        if 'state' in vals:
            for record in self:
                if vals['state'] == 'sold' and not record.selling_price:
                    vals['selling_price'] = record.expected_price
        return super().write(vals)
    
    # Action Methods
    def action_make_available(self):
        """Mark property as available"""
        for record in self:
            if record.state == 'draft':
                record.state = 'available'
                record.message_post(body=_('Property marked as available'))
    
    def action_receive_offer(self):
        """Mark property as having received offer"""
        for record in self:
            if record.state == 'available':
                record.state = 'offer_received'
                record.message_post(body=_('Offer received for property'))
    
    def action_accept_offer(self):
        """Mark property offer as accepted"""
        for record in self:
            if record.state == 'offer_received':
                record.state = 'offer_accepted'
                record.message_post(body=_('Offer accepted for property'))
    
    def action_sell_property(self):
        """Mark property as sold"""
        for record in self:
            if record.state == 'offer_accepted':
                record.state = 'sold'
                record.message_post(body=_('Property sold successfully'))
    
    def action_cancel_property(self):
        """Cancel property listing"""
        for record in self:
            if record.state not in ['sold', 'rented']:
                record.state = 'cancelled'
                record.message_post(body=_('Property listing cancelled'))
    
    # Utility Methods
    def get_portal_url(self):
        """Get portal URL for property"""
        return f'/my/property/{self.id}'
    
    def _get_coordinates_from_address(self):
        """Get GPS coordinates from address using geopy"""
        try:
            from geopy.geocoders import Nominatim
            geolocator = Nominatim(user_agent="odoo_real_estate")
            location = geolocator.geocode(self.full_address)
            if location:
                self.latitude = location.latitude
                self.longitude = location.longitude
        except Exception as e:
            _logger.warning(f"Geocoding failed for property {self.name}: {str(e)}")
    
    def action_get_coordinates(self):
        """Action to get GPS coordinates from address"""
        for record in self:
            record._get_coordinates_from_address()
        return True


class RealEstatePropertyOffer(models.Model):
    """Property Offers Model"""
    
    _name = 'real.estate.property.offer'
    _description = 'Property Offer'
    _order = 'price desc'
    
    price = fields.Monetary(
        string='Price',
        currency_field='currency_id',
        required=True
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        related='property_id.currency_id',
        store=True
    )
    
    status = fields.Selection([
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('refused', 'Refused'),
    ], string='Status', default='pending', required=True)
    
    partner_id = fields.Many2one(
        'res.partner',
        string='Partner',
        required=True
    )
    
    property_id = fields.Many2one(
        'real.estate.property',
        string='Property',
        required=True,
        ondelete='cascade'
    )
    
    validity = fields.Integer(
        string='Validity (Days)',
        default=7
    )
    
    date_deadline = fields.Date(
        string='Deadline',
        compute='_compute_date_deadline',
        inverse='_inverse_date_deadline'
    )
    
    notes = fields.Text(string='Notes')
    
    @api.depends('create_date', 'validity')
    def _compute_date_deadline(self):
        """Compute offer deadline"""
        for record in self:
            if record.create_date:
                record.date_deadline = record.create_date.date() + timedelta(days=record.validity)
            else:
                record.date_deadline = fields.Date.today() + timedelta(days=record.validity)
    
    def _inverse_date_deadline(self):
        """Inverse compute for deadline"""
        for record in self:
            if record.date_deadline and record.create_date:
                delta = record.date_deadline - record.create_date.date()
                record.validity = delta.days
    
    def action_accept(self):
        """Accept offer"""
        self.status = 'accepted'
        self.property_id.buyer_id = self.partner_id
        self.property_id.selling_price = self.price
        self.property_id.action_accept_offer()
    
    def action_refuse(self):
        """Refuse offer"""
        self.status = 'refused'


class RealEstatePropertyImage(models.Model):
    """Property Images Model"""
    
    _name = 'real.estate.property.image'
    _description = 'Property Image'
    _order = 'sequence, id'
    
    name = fields.Char(string='Name', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    
    image_1920 = fields.Image(
        string='Image',
        max_width=1920,
        max_height=1920,
        required=True
    )
    
    image_512 = fields.Image(
        string='Image 512',
        related='image_1920',
        max_width=512,
        max_height=512,
        store=True
    )
    
    image_128 = fields.Image(
        string='Image 128',
        related='image_1920',
        max_width=128,
        max_height=128,
        store=True
    )
    
    property_id = fields.Many2one(
        'real.estate.property',
        string='Property',
        required=True,
        ondelete='cascade'
    )
    
    description = fields.Text(string='Description')


class RealEstatePropertyDocument(models.Model):
    """Property Documents Model"""
    
    _name = 'real.estate.property.document'
    _description = 'Property Document'
    _order = 'create_date desc'
    
    name = fields.Char(string='Document Name', required=True)
    document = fields.Binary(string='Document', required=True)
    document_filename = fields.Char(string='Filename')
    
    document_type = fields.Selection([
        ('floor_plan', 'Floor Plan'),
        ('energy_certificate', 'Energy Certificate'),
        ('title_deed', 'Title Deed'),
        ('survey', 'Survey'),
        ('planning_permission', 'Planning Permission'),
        ('other', 'Other'),
    ], string='Document Type', required=True)
    
    property_id = fields.Many2one(
        'real.estate.property',
        string='Property',
        required=True,
        ondelete='cascade'
    )
    
    description = fields.Text(string='Description')
    is_public = fields.Boolean(string='Public Document', default=False)


class RealEstatePropertyFeature(models.Model):
    """Property Features Model"""
    
    _name = 'real.estate.property.feature'
    _description = 'Property Feature'
    _order = 'name'
    
    name = fields.Char(string='Feature Name', required=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True)
    
    feature_type = fields.Selection([
        ('interior', 'Interior'),
        ('exterior', 'Exterior'),
        ('amenity', 'Amenity'),
        ('security', 'Security'),
        ('other', 'Other'),
    ], string='Feature Type', required=True)