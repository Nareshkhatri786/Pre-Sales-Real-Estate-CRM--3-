# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class RealEstateContract(models.Model):
    """Real Estate Contract Model"""
    
    _name = 'real.estate.contract'
    _description = 'Real Estate Contract'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'contract_date desc'
    _rec_name = 'name'
    
    # Basic Information
    name = fields.Char(
        string='Contract Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
        help='Unique contract reference'
    )
    
    property_id = fields.Many2one(
        'real.estate.property',
        string='Property',
        required=True,
        tracking=True,
        help='Property subject of the contract'
    )
    
    # Contract Type
    contract_type = fields.Selection([
        ('sale', 'Sale Contract'),
        ('purchase', 'Purchase Contract'),
        ('rental', 'Rental Agreement'),
        ('lease', 'Lease Agreement'),
        ('option', 'Option to Purchase'),
        ('management', 'Property Management'),
    ], string='Contract Type', required=True, default='sale', tracking=True)
    
    # Parties
    seller_id = fields.Many2one(
        'res.partner',
        string='Seller',
        required=True,
        tracking=True,
        help='Seller party'
    )
    
    buyer_id = fields.Many2one(
        'res.partner',
        string='Buyer',
        required=True,
        tracking=True,
        help='Buyer party'
    )
    
    agent_id = fields.Many2one(
        'res.users',
        string='Agent',
        required=True,
        default=lambda self: self.env.user,
        tracking=True,
        help='Real estate agent'
    )
    
    # Contract Details
    contract_date = fields.Date(
        string='Contract Date',
        required=True,
        default=fields.Date.today,
        tracking=True,
        help='Date when contract was signed'
    )
    
    effective_date = fields.Date(
        string='Effective Date',
        help='Date when contract becomes effective'
    )
    
    completion_date = fields.Date(
        string='Completion Date',
        help='Expected completion/closing date'
    )
    
    # Financial Terms
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.company.currency_id
    )
    
    contract_price = fields.Monetary(
        string='Contract Price',
        currency_field='currency_id',
        required=True,
        tracking=True,
        help='Total contract price'
    )
    
    deposit_amount = fields.Monetary(
        string='Deposit Amount',
        currency_field='currency_id',
        help='Deposit amount paid'
    )
    
    deposit_percentage = fields.Float(
        string='Deposit %',
        compute='_compute_deposit_percentage',
        store=True,
        help='Deposit as percentage of contract price'
    )
    
    balance_due = fields.Monetary(
        string='Balance Due',
        currency_field='currency_id',
        compute='_compute_balance_due',
        store=True,
        help='Remaining balance due'
    )
    
    # Payment Terms
    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('mortgage', 'Mortgage'),
        ('installments', 'Installments'),
        ('mixed', 'Mixed'),
    ], string='Payment Method', default='mortgage')
    
    mortgage_contingent = fields.Boolean(
        string='Mortgage Contingent',
        default=True,
        help='Contract contingent on mortgage approval'
    )
    
    mortgage_amount = fields.Monetary(
        string='Mortgage Amount',
        currency_field='currency_id',
        help='Mortgage loan amount'
    )
    
    mortgage_deadline = fields.Date(
        string='Mortgage Deadline',
        help='Deadline for mortgage approval'
    )
    
    # Contingencies
    inspection_contingency = fields.Boolean(
        string='Inspection Contingency',
        default=True,
        help='Contract contingent on property inspection'
    )
    
    inspection_deadline = fields.Date(
        string='Inspection Deadline',
        help='Deadline for property inspection'
    )
    
    appraisal_contingency = fields.Boolean(
        string='Appraisal Contingency',
        default=True,
        help='Contract contingent on property appraisal'
    )
    
    appraisal_deadline = fields.Date(
        string='Appraisal Deadline',
        help='Deadline for property appraisal'
    )
    
    other_contingencies = fields.Text(
        string='Other Contingencies',
        help='Additional contingencies'
    )
    
    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending Signatures'),
        ('signed', 'Signed'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('terminated', 'Terminated'),
    ], string='Status', default='draft', required=True, tracking=True)
    
    # Commission
    commission_rate = fields.Float(
        string='Commission Rate (%)',
        default=5.0,
        help='Commission rate percentage'
    )
    
    commission_amount = fields.Monetary(
        string='Commission Amount',
        currency_field='currency_id',
        compute='_compute_commission_amount',
        store=True,
        help='Total commission amount'
    )
    
    commission_split = fields.Selection([
        ('full', 'Full to Agent'),
        ('shared', 'Shared with Company'),
        ('custom', 'Custom Split'),
    ], string='Commission Split', default='shared')
    
    agent_commission_rate = fields.Float(
        string='Agent Commission Rate (%)',
        default=50.0,
        help='Agent share of commission'
    )
    
    # Documents
    contract_document = fields.Binary(
        string='Contract Document',
        help='Signed contract document'
    )
    
    contract_document_filename = fields.Char(
        string='Contract Filename'
    )
    
    supporting_documents = fields.Many2many(
        'ir.attachment',
        'contract_document_rel',
        'contract_id',
        'attachment_id',
        string='Supporting Documents'
    )
    
    # Terms and Conditions
    special_conditions = fields.Html(
        string='Special Conditions',
        help='Special terms and conditions'
    )
    
    inclusions = fields.Text(
        string='Inclusions',
        help='Items included in the sale'
    )
    
    exclusions = fields.Text(
        string='Exclusions',
        help='Items excluded from the sale'
    )
    
    # Legal Information
    legal_description = fields.Text(
        string='Legal Description',
        help='Legal property description'
    )
    
    title_company = fields.Char(
        string='Title Company',
        help='Title insurance company'
    )
    
    attorney_buyer = fields.Char(
        string='Buyer Attorney',
        help='Buyer legal representation'
    )
    
    attorney_seller = fields.Char(
        string='Seller Attorney',
        help='Seller legal representation'
    )
    
    # Milestones and Tasks
    milestone_ids = fields.One2many(
        'real.estate.contract.milestone',
        'contract_id',
        string='Milestones'
    )
    
    # Progress Tracking
    progress_percentage = fields.Float(
        string='Progress %',
        compute='_compute_progress',
        help='Contract completion progress'
    )
    
    days_to_completion = fields.Integer(
        string='Days to Completion',
        compute='_compute_days_to_completion',
        help='Days until completion date'
    )
    
    # Relations
    invoice_ids = fields.One2many(
        'account.move',
        'contract_id',
        string='Invoices'
    )
    
    commission_record_id = fields.Many2one(
        'real.estate.commission',
        string='Commission Record',
        help='Related commission record'
    )
    
    @api.depends('contract_price', 'deposit_amount')
    def _compute_deposit_percentage(self):
        """Compute deposit percentage"""
        for record in self:
            if record.contract_price > 0:
                record.deposit_percentage = (record.deposit_amount / record.contract_price) * 100
            else:
                record.deposit_percentage = 0
    
    @api.depends('contract_price', 'deposit_amount')
    def _compute_balance_due(self):
        """Compute balance due"""
        for record in self:
            record.balance_due = record.contract_price - record.deposit_amount
    
    @api.depends('contract_price', 'commission_rate')
    def _compute_commission_amount(self):
        """Compute commission amount"""
        for record in self:
            record.commission_amount = (record.contract_price * record.commission_rate) / 100
    
    @api.depends('milestone_ids', 'milestone_ids.completed')
    def _compute_progress(self):
        """Compute contract progress based on milestones"""
        for record in self:
            if record.milestone_ids:
                completed_milestones = record.milestone_ids.filtered('completed')
                record.progress_percentage = (len(completed_milestones) / len(record.milestone_ids)) * 100
            else:
                record.progress_percentage = 0
    
    @api.depends('completion_date')
    def _compute_days_to_completion(self):
        """Compute days until completion"""
        today = fields.Date.today()
        for record in self:
            if record.completion_date:
                delta = record.completion_date - today
                record.days_to_completion = delta.days
            else:
                record.days_to_completion = 0
    
    @api.model
    def create(self, vals):
        """Override create to generate sequence and create milestones"""
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('real.estate.contract') or _('New')
        
        contract = super().create(vals)
        contract._create_default_milestones()
        return contract
    
    def _create_default_milestones(self):
        """Create default milestones based on contract type"""
        self.ensure_one()
        
        milestone_data = []
        
        if self.contract_type in ['sale', 'purchase']:
            milestone_data = [
                {'name': 'Contract Signed', 'sequence': 1, 'deadline_days': 0},
                {'name': 'Mortgage Application', 'sequence': 2, 'deadline_days': 7},
                {'name': 'Property Inspection', 'sequence': 3, 'deadline_days': 14},
                {'name': 'Property Appraisal', 'sequence': 4, 'deadline_days': 21},
                {'name': 'Mortgage Approval', 'sequence': 5, 'deadline_days': 30},
                {'name': 'Final Walkthrough', 'sequence': 6, 'deadline_days': 44},
                {'name': 'Closing/Settlement', 'sequence': 7, 'deadline_days': 45},
            ]
        elif self.contract_type in ['rental', 'lease']:
            milestone_data = [
                {'name': 'Lease Signed', 'sequence': 1, 'deadline_days': 0},
                {'name': 'Security Deposit Paid', 'sequence': 2, 'deadline_days': 3},
                {'name': 'Property Inspection', 'sequence': 3, 'deadline_days': 7},
                {'name': 'Keys Handed Over', 'sequence': 4, 'deadline_days': 14},
            ]
        
        for milestone in milestone_data:
            milestone['contract_id'] = self.id
            if milestone['deadline_days'] > 0:
                milestone['deadline_date'] = self.contract_date + timedelta(days=milestone['deadline_days'])
            else:
                milestone['deadline_date'] = self.contract_date
            
            del milestone['deadline_days']
            self.env['real.estate.contract.milestone'].create(milestone)
    
    @api.constrains('contract_price', 'deposit_amount')
    def _check_amounts(self):
        """Validate contract amounts"""
        for record in self:
            if record.contract_price <= 0:
                raise ValidationError(_('Contract price must be positive'))
            if record.deposit_amount > record.contract_price:
                raise ValidationError(_('Deposit amount cannot exceed contract price'))
    
    def action_send_for_signature(self):
        """Send contract for signature"""
        for record in self:
            if record.state == 'draft':
                record.state = 'pending'
                record.message_post(body=_('Contract sent for signature'))
    
    def action_sign_contract(self):
        """Sign contract"""
        for record in self:
            if record.state == 'pending':
                record.state = 'signed'
                record.message_post(body=_('Contract signed'))
    
    def action_activate_contract(self):
        """Activate contract"""
        for record in self:
            if record.state == 'signed':
                record.state = 'active'
                record.effective_date = fields.Date.today()
                record.message_post(body=_('Contract activated'))
    
    def action_complete_contract(self):
        """Complete contract"""
        for record in self:
            if record.state == 'active':
                record.state = 'completed'
                record.message_post(body=_('Contract completed'))
                # Create commission record
                record._create_commission_record()
    
    def action_cancel_contract(self):
        """Cancel contract"""
        for record in self:
            if record.state not in ['completed']:
                record.state = 'cancelled'
                record.message_post(body=_('Contract cancelled'))
    
    def _create_commission_record(self):
        """Create commission record when contract is completed"""
        self.ensure_one()
        
        if self.commission_record_id:
            return  # Commission already created
        
        commission_vals = {
            'name': f'Commission - {self.name}',
            'contract_id': self.id,
            'agent_id': self.env['real.estate.agent'].search([('user_id', '=', self.agent_id.id)], limit=1).id,
            'property_id': self.property_id.id,
            'commission_type': 'sale' if self.contract_type in ['sale', 'purchase'] else 'rental',
            'sale_amount': self.contract_price,
            'commission_rate': self.commission_rate,
            'commission_amount': self.commission_amount,
            'agent_rate': self.agent_commission_rate,
            'agent_amount': (self.commission_amount * self.agent_commission_rate) / 100,
            'date_earned': fields.Date.today(),
            'state': 'earned',
        }
        
        commission = self.env['real.estate.commission'].create(commission_vals)
        self.commission_record_id = commission
    
    def action_generate_invoice(self):
        """Generate invoice for contract"""
        self.ensure_one()
        
        # Create invoice for the contract
        invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': self.buyer_id.id,
            'contract_id': self.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [(0, 0, {
                'name': f'Real Estate Transaction - {self.property_id.name}',
                'quantity': 1,
                'price_unit': self.contract_price,
                'account_id': self.env['account.account'].search([
                    ('user_type_id.name', '=', 'Income')
                ], limit=1).id,
            })],
        }
        
        invoice = self.env['account.move'].create(invoice_vals)
        
        return {
            'name': _('Invoice'),
            'view_mode': 'form',
            'res_model': 'account.move',
            'res_id': invoice.id,
            'type': 'ir.actions.act_window',
        }


class RealEstateContractMilestone(models.Model):
    """Contract Milestones"""
    
    _name = 'real.estate.contract.milestone'
    _description = 'Contract Milestone'
    _order = 'sequence, deadline_date'
    
    name = fields.Char(
        string='Milestone',
        required=True,
        help='Milestone description'
    )
    
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Milestone order'
    )
    
    contract_id = fields.Many2one(
        'real.estate.contract',
        string='Contract',
        required=True,
        ondelete='cascade'
    )
    
    deadline_date = fields.Date(
        string='Deadline',
        help='Milestone deadline'
    )
    
    completed = fields.Boolean(
        string='Completed',
        default=False
    )
    
    completion_date = fields.Date(
        string='Completion Date',
        help='When milestone was completed'
    )
    
    responsible_party = fields.Selection([
        ('buyer', 'Buyer'),
        ('seller', 'Seller'),
        ('agent', 'Agent'),
        ('lender', 'Lender'),
        ('attorney', 'Attorney'),
        ('other', 'Other'),
    ], string='Responsible Party')
    
    notes = fields.Text(
        string='Notes',
        help='Milestone notes and comments'
    )
    
    is_overdue = fields.Boolean(
        string='Overdue',
        compute='_compute_is_overdue',
        help='Whether milestone is overdue'
    )
    
    @api.depends('deadline_date', 'completed')
    def _compute_is_overdue(self):
        """Check if milestone is overdue"""
        today = fields.Date.today()
        for record in self:
            record.is_overdue = (
                not record.completed and
                record.deadline_date and
                record.deadline_date < today
            )
    
    def action_complete(self):
        """Mark milestone as completed"""
        for record in self:
            record.completed = True
            record.completion_date = fields.Date.today()
    
    def action_reopen(self):
        """Reopen milestone"""
        for record in self:
            record.completed = False
            record.completion_date = False