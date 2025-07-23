# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class RealEstateValuation(models.Model):
    """Property Valuation Model"""
    
    _name = 'real.estate.valuation'
    _description = 'Property Valuation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'valuation_date desc'
    _rec_name = 'name'
    
    # Basic Information
    name = fields.Char(
        string='Valuation Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
        help='Unique valuation reference'
    )
    
    property_id = fields.Many2one(
        'real.estate.property',
        string='Property',
        required=True,
        help='Property being valuated'
    )
    
    # Valuation Details
    valuation_date = fields.Date(
        string='Valuation Date',
        required=True,
        default=fields.Date.today,
        tracking=True
    )
    
    valuation_type = fields.Selection([
        ('market', 'Market Valuation'),
        ('insurance', 'Insurance Valuation'),
        ('mortgage', 'Mortgage Valuation'),
        ('tax', 'Tax Assessment'),
        ('rental', 'Rental Valuation'),
        ('investment', 'Investment Valuation'),
    ], string='Valuation Type', required=True, default='market')
    
    purpose = fields.Selection([
        ('sale', 'Sale'),
        ('purchase', 'Purchase'),
        ('mortgage', 'Mortgage'),
        ('insurance', 'Insurance'),
        ('tax', 'Tax Assessment'),
        ('legal', 'Legal Purposes'),
        ('investment', 'Investment Analysis'),
    ], string='Purpose', required=True)
    
    # Valuer Information
    valuer_id = fields.Many2one(
        'res.users',
        string='Valuer',
        required=True,
        default=lambda self: self.env.user,
        tracking=True
    )
    
    external_valuer = fields.Char(
        string='External Valuer',
        help='External valuation company/person'
    )
    
    valuer_license = fields.Char(
        string='Valuer License',
        help='Professional license number'
    )
    
    # Valuation Amount
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.company.currency_id
    )
    
    estimated_value = fields.Monetary(
        string='Estimated Value',
        currency_field='currency_id',
        required=True,
        tracking=True,
        help='Estimated property value'
    )
    
    confidence_level = fields.Selection([
        ('low', 'Low (±20%)'),
        ('medium', 'Medium (±10%)'),
        ('high', 'High (±5%)'),
        ('very_high', 'Very High (±2%)'),
    ], string='Confidence Level', default='medium', required=True)
    
    # Valuation Range
    min_value = fields.Monetary(
        string='Minimum Value',
        currency_field='currency_id',
        compute='_compute_value_range',
        store=True
    )
    
    max_value = fields.Monetary(
        string='Maximum Value',
        currency_field='currency_id',
        compute='_compute_value_range',
        store=True
    )
    
    # Methodology
    valuation_method = fields.Selection([
        ('comparative', 'Comparative Market Analysis'),
        ('cost', 'Cost Approach'),
        ('income', 'Income Approach'),
        ('residual', 'Residual Method'),
        ('profits', 'Profits Method'),
        ('hybrid', 'Hybrid Approach'),
    ], string='Valuation Method', required=True, default='comparative')
    
    methodology_notes = fields.Html(
        string='Methodology Notes',
        help='Detailed explanation of valuation methodology'
    )
    
    # Comparable Properties
    comparable_ids = fields.One2many(
        'real.estate.valuation.comparable',
        'valuation_id',
        string='Comparable Properties'
    )
    
    # Market Conditions
    market_conditions = fields.Selection([
        ('declining', 'Declining Market'),
        ('stable', 'Stable Market'),
        ('improving', 'Improving Market'),
        ('volatile', 'Volatile Market'),
    ], string='Market Conditions', default='stable')
    
    market_notes = fields.Text(
        string='Market Analysis',
        help='Analysis of current market conditions'
    )
    
    # Property Condition Assessment
    property_condition = fields.Selection([
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
        ('needs_renovation', 'Needs Renovation'),
    ], string='Property Condition', required=True)
    
    condition_notes = fields.Text(
        string='Condition Notes',
        help='Detailed notes on property condition'
    )
    
    # Adjustments
    location_adjustment = fields.Float(
        string='Location Adjustment (%)',
        default=0.0,
        help='Adjustment for location factors'
    )
    
    size_adjustment = fields.Float(
        string='Size Adjustment (%)',
        default=0.0,
        help='Adjustment for size differences'
    )
    
    condition_adjustment = fields.Float(
        string='Condition Adjustment (%)',
        default=0.0,
        help='Adjustment for property condition'
    )
    
    other_adjustments = fields.Float(
        string='Other Adjustments (%)',
        default=0.0,
        help='Other miscellaneous adjustments'
    )
    
    total_adjustment = fields.Float(
        string='Total Adjustment (%)',
        compute='_compute_total_adjustment',
        store=True,
        help='Sum of all adjustments'
    )
    
    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('reviewed', 'Reviewed'),
        ('approved', 'Approved'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', required=True, tracking=True)
    
    # Validity
    valid_until = fields.Date(
        string='Valid Until',
        help='Valuation validity period'
    )
    
    is_expired = fields.Boolean(
        string='Expired',
        compute='_compute_is_expired',
        help='Whether valuation has expired'
    )
    
    # Documents
    valuation_report = fields.Binary(
        string='Valuation Report',
        help='Detailed valuation report document'
    )
    
    valuation_report_filename = fields.Char(
        string='Report Filename'
    )
    
    supporting_documents = fields.Many2many(
        'ir.attachment',
        'valuation_document_rel',
        'valuation_id',
        'attachment_id',
        string='Supporting Documents'
    )
    
    # Notes and Comments
    description = fields.Html(
        string='Description',
        help='Valuation description and summary'
    )
    
    internal_notes = fields.Text(
        string='Internal Notes',
        help='Internal notes for valuers'
    )
    
    @api.depends('estimated_value', 'confidence_level')
    def _compute_value_range(self):
        """Compute valuation range based on confidence level"""
        confidence_margins = {
            'low': 0.20,
            'medium': 0.10,
            'high': 0.05,
            'very_high': 0.02,
        }
        
        for record in self:
            margin = confidence_margins.get(record.confidence_level, 0.10)
            margin_amount = record.estimated_value * margin
            record.min_value = record.estimated_value - margin_amount
            record.max_value = record.estimated_value + margin_amount
    
    @api.depends(
        'location_adjustment', 'size_adjustment',
        'condition_adjustment', 'other_adjustments'
    )
    def _compute_total_adjustment(self):
        """Compute total adjustment percentage"""
        for record in self:
            record.total_adjustment = (
                record.location_adjustment +
                record.size_adjustment +
                record.condition_adjustment +
                record.other_adjustments
            )
    
    @api.depends('valid_until')
    def _compute_is_expired(self):
        """Check if valuation has expired"""
        today = fields.Date.today()
        for record in self:
            record.is_expired = record.valid_until and record.valid_until < today
    
    @api.model
    def create(self, vals):
        """Override create to generate sequence"""
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('real.estate.valuation') or _('New')
        return super().create(vals)
    
    @api.constrains('estimated_value')
    def _check_estimated_value(self):
        """Validate estimated value"""
        for record in self:
            if record.estimated_value <= 0:
                raise ValidationError(_('Estimated value must be positive'))
    
    @api.constrains('valuation_date')
    def _check_valuation_date(self):
        """Validate valuation date"""
        for record in self:
            if record.valuation_date > fields.Date.today():
                raise ValidationError(_('Valuation date cannot be in the future'))
    
    def action_start_valuation(self):
        """Start valuation process"""
        for record in self:
            if record.state == 'draft':
                record.state = 'in_progress'
    
    def action_complete_valuation(self):
        """Complete valuation"""
        for record in self:
            if record.state == 'in_progress':
                record.state = 'completed'
                record.message_post(body=_('Valuation completed'))
    
    def action_review_valuation(self):
        """Review valuation"""
        for record in self:
            if record.state == 'completed':
                record.state = 'reviewed'
    
    def action_approve_valuation(self):
        """Approve valuation"""
        for record in self:
            if record.state == 'reviewed':
                record.state = 'approved'
                record.message_post(body=_('Valuation approved'))
    
    def action_cancel_valuation(self):
        """Cancel valuation"""
        for record in self:
            if record.state not in ['approved']:
                record.state = 'cancelled'
    
    def generate_report(self):
        """Generate valuation report"""
        self.ensure_one()
        
        # This would generate a PDF report
        return self.env.ref('real_estate_crm.report_property_valuation').report_action(self)


class RealEstateValuationComparable(models.Model):
    """Comparable Properties for Valuation"""
    
    _name = 'real.estate.valuation.comparable'
    _description = 'Valuation Comparable Property'
    _order = 'sequence, sale_date desc'
    
    sequence = fields.Integer(string='Sequence', default=10)
    
    valuation_id = fields.Many2one(
        'real.estate.valuation',
        string='Valuation',
        required=True,
        ondelete='cascade'
    )
    
    # Property Details
    address = fields.Char(
        string='Address',
        required=True,
        help='Comparable property address'
    )
    
    property_type = fields.Char(
        string='Property Type',
        help='Type of comparable property'
    )
    
    bedrooms = fields.Integer(string='Bedrooms')
    bathrooms = fields.Integer(string='Bathrooms')
    living_area = fields.Float(string='Living Area (sqm)')
    total_area = fields.Float(string='Total Area (sqm)')
    
    # Sale Information
    sale_price = fields.Monetary(
        string='Sale Price',
        currency_field='currency_id',
        required=True
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        related='valuation_id.currency_id',
        store=True
    )
    
    sale_date = fields.Date(
        string='Sale Date',
        required=True
    )
    
    price_per_sqm = fields.Monetary(
        string='Price per sqm',
        currency_field='currency_id',
        compute='_compute_price_per_sqm',
        store=True
    )
    
    # Adjustments
    location_factor = fields.Float(
        string='Location Factor',
        default=1.0,
        help='Location adjustment factor'
    )
    
    size_factor = fields.Float(
        string='Size Factor',
        default=1.0,
        help='Size adjustment factor'
    )
    
    condition_factor = fields.Float(
        string='Condition Factor',
        default=1.0,
        help='Condition adjustment factor'
    )
    
    time_factor = fields.Float(
        string='Time Factor',
        default=1.0,
        help='Time/market adjustment factor'
    )
    
    adjusted_price = fields.Monetary(
        string='Adjusted Price',
        currency_field='currency_id',
        compute='_compute_adjusted_price',
        store=True
    )
    
    # Additional Information
    distance_km = fields.Float(
        string='Distance (km)',
        help='Distance from subject property'
    )
    
    source = fields.Char(
        string='Source',
        help='Information source'
    )
    
    notes = fields.Text(
        string='Notes',
        help='Additional notes about this comparable'
    )
    
    @api.depends('sale_price', 'total_area')
    def _compute_price_per_sqm(self):
        """Compute price per square meter"""
        for record in self:
            if record.total_area > 0:
                record.price_per_sqm = record.sale_price / record.total_area
            else:
                record.price_per_sqm = 0
    
    @api.depends(
        'sale_price', 'location_factor', 'size_factor',
        'condition_factor', 'time_factor'
    )
    def _compute_adjusted_price(self):
        """Compute adjusted price after applying all factors"""
        for record in self:
            total_factor = (
                record.location_factor *
                record.size_factor *
                record.condition_factor *
                record.time_factor
            )
            record.adjusted_price = record.sale_price * total_factor