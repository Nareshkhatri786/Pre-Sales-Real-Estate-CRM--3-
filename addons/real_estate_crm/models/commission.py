# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class RealEstateCommission(models.Model):
    """Real Estate Commission Model"""
    
    _name = 'real.estate.commission'
    _description = 'Real Estate Commission'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_earned desc'
    _rec_name = 'name'
    
    # Basic Information
    name = fields.Char(
        string='Commission Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
        help='Unique commission reference'
    )
    
    # Related Records
    agent_id = fields.Many2one(
        'real.estate.agent',
        string='Agent',
        required=True,
        tracking=True,
        help='Agent earning the commission'
    )
    
    property_id = fields.Many2one(
        'real.estate.property',
        string='Property',
        required=True,
        tracking=True,
        help='Property related to commission'
    )
    
    contract_id = fields.Many2one(
        'real.estate.contract',
        string='Contract',
        help='Related contract'
    )
    
    # Commission Type
    commission_type = fields.Selection([
        ('sale', 'Sale Commission'),
        ('rental', 'Rental Commission'),
        ('management', 'Management Commission'),
        ('referral', 'Referral Commission'),
        ('bonus', 'Bonus Commission'),
    ], string='Type', required=True, default='sale', tracking=True)
    
    # Financial Details
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.company.currency_id
    )
    
    sale_amount = fields.Monetary(
        string='Sale Amount',
        currency_field='currency_id',
        required=True,
        tracking=True,
        help='Total sale/rental amount'
    )
    
    commission_rate = fields.Float(
        string='Commission Rate (%)',
        required=True,
        default=5.0,
        tracking=True,
        help='Commission rate percentage'
    )
    
    commission_amount = fields.Monetary(
        string='Total Commission',
        currency_field='currency_id',
        compute='_compute_commission_amount',
        store=True,
        help='Gross commission amount'
    )
    
    # Agent Split
    agent_rate = fields.Float(
        string='Agent Rate (%)',
        default=50.0,
        help='Agent share percentage'
    )
    
    agent_amount = fields.Monetary(
        string='Agent Amount',
        currency_field='currency_id',
        compute='_compute_agent_amount',
        store=True,
        help='Agent commission amount'
    )
    
    company_amount = fields.Monetary(
        string='Company Amount',
        currency_field='currency_id',
        compute='_compute_company_amount',
        store=True,
        help='Company commission amount'
    )
    
    # Deductions
    deduction_ids = fields.One2many(
        'real.estate.commission.deduction',
        'commission_id',
        string='Deductions'
    )
    
    total_deductions = fields.Monetary(
        string='Total Deductions',
        currency_field='currency_id',
        compute='_compute_total_deductions',
        store=True,
        help='Total deduction amount'
    )
    
    net_agent_amount = fields.Monetary(
        string='Net Agent Amount',
        currency_field='currency_id',
        compute='_compute_net_agent_amount',
        store=True,
        help='Agent amount after deductions'
    )
    
    # Dates
    date_earned = fields.Date(
        string='Date Earned',
        required=True,
        default=fields.Date.today,
        tracking=True,
        help='Date commission was earned'
    )
    
    date_paid = fields.Date(
        string='Date Paid',
        tracking=True,
        help='Date commission was paid'
    )
    
    payment_due_date = fields.Date(
        string='Payment Due Date',
        compute='_compute_payment_due_date',
        store=True,
        help='Date when payment is due'
    )
    
    # Status
    state = fields.Selection([
        ('pending', 'Pending'),
        ('earned', 'Earned'),
        ('approved', 'Approved'),
        ('paid', 'Paid'),
        ('disputed', 'Disputed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='pending', required=True, tracking=True)
    
    # Payment Information
    payment_method = fields.Selection([
        ('bank_transfer', 'Bank Transfer'),
        ('check', 'Check'),
        ('cash', 'Cash'),
        ('payroll', 'Payroll'),
        ('other', 'Other'),
    ], string='Payment Method')
    
    payment_reference = fields.Char(
        string='Payment Reference',
        help='Payment transaction reference'
    )
    
    # Tax Information
    tax_year = fields.Integer(
        string='Tax Year',
        compute='_compute_tax_year',
        store=True,
        help='Tax year for commission'
    )
    
    tax_category = fields.Selection([
        ('1099', '1099 Contractor'),
        ('w2', 'W-2 Employee'),
        ('exempt', 'Tax Exempt'),
    ], string='Tax Category', default='1099')
    
    # Additional Information
    description = fields.Html(
        string='Description',
        help='Commission description and notes'
    )
    
    internal_notes = fields.Text(
        string='Internal Notes',
        help='Internal notes about commission'
    )
    
    # Split with Other Agents
    split_commission = fields.Boolean(
        string='Split Commission',
        default=False,
        help='Commission split with other agents'
    )
    
    split_agent_ids = fields.One2many(
        'real.estate.commission.split',
        'commission_id',
        string='Commission Splits'
    )
    
    # Performance Metrics
    is_overdue = fields.Boolean(
        string='Payment Overdue',
        compute='_compute_is_overdue',
        help='Whether payment is overdue'
    )
    
    days_outstanding = fields.Integer(
        string='Days Outstanding',
        compute='_compute_days_outstanding',
        help='Days since commission was earned'
    )
    
    # Relations
    invoice_id = fields.Many2one(
        'account.move',
        string='Invoice',
        help='Related invoice for commission payment'
    )
    
    @api.depends('sale_amount', 'commission_rate')
    def _compute_commission_amount(self):
        """Compute total commission amount"""
        for record in self:
            record.commission_amount = (record.sale_amount * record.commission_rate) / 100
    
    @api.depends('commission_amount', 'agent_rate')
    def _compute_agent_amount(self):
        """Compute agent commission amount"""
        for record in self:
            record.agent_amount = (record.commission_amount * record.agent_rate) / 100
    
    @api.depends('commission_amount', 'agent_amount')
    def _compute_company_amount(self):
        """Compute company commission amount"""
        for record in self:
            record.company_amount = record.commission_amount - record.agent_amount
    
    @api.depends('deduction_ids.amount')
    def _compute_total_deductions(self):
        """Compute total deductions"""
        for record in self:
            record.total_deductions = sum(record.deduction_ids.mapped('amount'))
    
    @api.depends('agent_amount', 'total_deductions')
    def _compute_net_agent_amount(self):
        """Compute net agent amount after deductions"""
        for record in self:
            record.net_agent_amount = record.agent_amount - record.total_deductions
    
    @api.depends('date_earned')
    def _compute_payment_due_date(self):
        """Compute payment due date (30 days after earned)"""
        for record in self:
            if record.date_earned:
                record.payment_due_date = record.date_earned + timedelta(days=30)
            else:
                record.payment_due_date = False
    
    @api.depends('date_earned')
    def _compute_tax_year(self):
        """Compute tax year based on date earned"""
        for record in self:
            if record.date_earned:
                record.tax_year = record.date_earned.year
            else:
                record.tax_year = datetime.now().year
    
    @api.depends('payment_due_date', 'date_paid', 'state')
    def _compute_is_overdue(self):
        """Check if payment is overdue"""
        today = fields.Date.today()
        for record in self:
            record.is_overdue = (
                record.state in ['earned', 'approved'] and
                record.payment_due_date and
                record.payment_due_date < today and
                not record.date_paid
            )
    
    @api.depends('date_earned', 'date_paid')
    def _compute_days_outstanding(self):
        """Compute days outstanding"""
        for record in self:
            if record.date_earned:
                end_date = record.date_paid or fields.Date.today()
                delta = end_date - record.date_earned
                record.days_outstanding = delta.days
            else:
                record.days_outstanding = 0
    
    @api.model
    def create(self, vals):
        """Override create to generate sequence"""
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('real.estate.commission') or _('New')
        return super().create(vals)
    
    @api.constrains('commission_rate', 'agent_rate')
    def _check_rates(self):
        """Validate commission rates"""
        for record in self:
            if record.commission_rate < 0 or record.commission_rate > 100:
                raise ValidationError(_('Commission rate must be between 0 and 100'))
            if record.agent_rate < 0 or record.agent_rate > 100:
                raise ValidationError(_('Agent rate must be between 0 and 100'))
    
    @api.constrains('sale_amount')
    def _check_sale_amount(self):
        """Validate sale amount"""
        for record in self:
            if record.sale_amount <= 0:
                raise ValidationError(_('Sale amount must be positive'))
    
    def action_approve(self):
        """Approve commission"""
        for record in self:
            if record.state == 'earned':
                record.state = 'approved'
                record.message_post(body=_('Commission approved'))
    
    def action_pay(self):
        """Mark commission as paid"""
        for record in self:
            if record.state == 'approved':
                record.state = 'paid'
                record.date_paid = fields.Date.today()
                record.message_post(body=_('Commission paid'))
    
    def action_dispute(self):
        """Mark commission as disputed"""
        for record in self:
            if record.state in ['earned', 'approved']:
                record.state = 'disputed'
                record.message_post(body=_('Commission disputed'))
    
    def action_cancel(self):
        """Cancel commission"""
        for record in self:
            if record.state not in ['paid']:
                record.state = 'cancelled'
                record.message_post(body=_('Commission cancelled'))
    
    def action_create_invoice(self):
        """Create invoice for commission payment"""
        self.ensure_one()
        
        if self.invoice_id:
            raise ValidationError(_('Invoice already exists for this commission'))
        
        # Create vendor bill for commission payment
        invoice_vals = {
            'move_type': 'in_invoice',
            'partner_id': self.agent_id.partner_id.id if self.agent_id.partner_id else self.agent_id.user_id.partner_id.id,
            'invoice_date': fields.Date.today(),
            'commission_id': self.id,
            'invoice_line_ids': [(0, 0, {
                'name': f'Commission - {self.name}',
                'quantity': 1,
                'price_unit': self.net_agent_amount,
                'account_id': self.env['account.account'].search([
                    ('user_type_id.name', '=', 'Expenses')
                ], limit=1).id,
            })],
        }
        
        invoice = self.env['account.move'].create(invoice_vals)
        self.invoice_id = invoice
        
        return {
            'name': _('Commission Invoice'),
            'view_mode': 'form',
            'res_model': 'account.move',
            'res_id': invoice.id,
            'type': 'ir.actions.act_window',
        }
    
    def get_commission_report_data(self):
        """Get data for commission reports"""
        self.ensure_one()
        
        return {
            'agent_name': self.agent_id.name,
            'property_address': self.property_id.full_address,
            'sale_amount': self.sale_amount,
            'commission_rate': self.commission_rate,
            'commission_amount': self.commission_amount,
            'agent_amount': self.agent_amount,
            'net_amount': self.net_agent_amount,
            'date_earned': self.date_earned,
            'date_paid': self.date_paid,
            'deductions': self.deduction_ids.mapped(lambda d: {
                'type': d.deduction_type,
                'amount': d.amount,
                'description': d.description
            })
        }


class RealEstateCommissionDeduction(models.Model):
    """Commission Deductions"""
    
    _name = 'real.estate.commission.deduction'
    _description = 'Commission Deduction'
    _order = 'sequence, name'
    
    sequence = fields.Integer(string='Sequence', default=10)
    
    commission_id = fields.Many2one(
        'real.estate.commission',
        string='Commission',
        required=True,
        ondelete='cascade'
    )
    
    name = fields.Char(
        string='Description',
        required=True,
        help='Deduction description'
    )
    
    deduction_type = fields.Selection([
        ('marketing', 'Marketing Costs'),
        ('admin', 'Administrative Fee'),
        ('insurance', 'Insurance'),
        ('tax', 'Tax Withholding'),
        ('advance', 'Advance Payment'),
        ('other', 'Other'),
    ], string='Type', required=True, default='other')
    
    amount = fields.Monetary(
        string='Amount',
        currency_field='currency_id',
        required=True,
        help='Deduction amount'
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        related='commission_id.currency_id',
        store=True
    )
    
    percentage = fields.Float(
        string='Percentage',
        help='Deduction as percentage of commission'
    )
    
    description = fields.Text(
        string='Notes',
        help='Additional notes about deduction'
    )
    
    @api.constrains('amount')
    def _check_amount(self):
        """Validate deduction amount"""
        for record in self:
            if record.amount < 0:
                raise ValidationError(_('Deduction amount cannot be negative'))


class RealEstateCommissionSplit(models.Model):
    """Commission Split with Other Agents"""
    
    _name = 'real.estate.commission.split'
    _description = 'Commission Split'
    _order = 'sequence, agent_id'
    
    sequence = fields.Integer(string='Sequence', default=10)
    
    commission_id = fields.Many2one(
        'real.estate.commission',
        string='Commission',
        required=True,
        ondelete='cascade'
    )
    
    agent_id = fields.Many2one(
        'real.estate.agent',
        string='Agent',
        required=True,
        help='Agent receiving split'
    )
    
    split_type = fields.Selection([
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    ], string='Split Type', default='percentage', required=True)
    
    percentage = fields.Float(
        string='Percentage',
        help='Split percentage'
    )
    
    fixed_amount = fields.Monetary(
        string='Fixed Amount',
        currency_field='currency_id',
        help='Fixed split amount'
    )
    
    split_amount = fields.Monetary(
        string='Split Amount',
        currency_field='currency_id',
        compute='_compute_split_amount',
        store=True,
        help='Calculated split amount'
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        related='commission_id.currency_id',
        store=True
    )
    
    role = fields.Char(
        string='Role',
        help='Agent role in transaction'
    )
    
    notes = fields.Text(
        string='Notes',
        help='Split notes'
    )
    
    @api.depends('split_type', 'percentage', 'fixed_amount', 'commission_id.agent_amount')
    def _compute_split_amount(self):
        """Compute split amount"""
        for record in self:
            if record.split_type == 'percentage':
                record.split_amount = (record.commission_id.agent_amount * record.percentage) / 100
            else:
                record.split_amount = record.fixed_amount
    
    @api.constrains('percentage')
    def _check_percentage(self):
        """Validate split percentage"""
        for record in self:
            if record.split_type == 'percentage':
                if record.percentage < 0 or record.percentage > 100:
                    raise ValidationError(_('Split percentage must be between 0 and 100'))