# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class RealEstateAppointment(models.Model):
    """Real Estate Appointment Model"""
    
    _name = 'real.estate.appointment'
    _description = 'Real Estate Appointment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'appointment_date desc'
    _rec_name = 'name'
    
    # Basic Information
    name = fields.Char(
        string='Subject',
        required=True,
        tracking=True,
        help='Appointment subject'
    )
    
    reference = fields.Char(
        string='Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
        help='Unique appointment reference'
    )
    
    # Participants
    agent_id = fields.Many2one(
        'res.users',
        string='Agent',
        required=True,
        default=lambda self: self.env.user,
        tracking=True,
        help='Real estate agent handling the appointment'
    )
    
    client_id = fields.Many2one(
        'res.partner',
        string='Client',
        required=True,
        tracking=True,
        help='Client for the appointment'
    )
    
    additional_attendees = fields.Many2many(
        'res.partner',
        'appointment_attendee_rel',
        'appointment_id',
        'partner_id',
        string='Additional Attendees',
        help='Additional people attending the appointment'
    )
    
    # Appointment Details
    appointment_type = fields.Selection([
        ('property_viewing', 'Property Viewing'),
        ('consultation', 'Consultation'),
        ('signing', 'Contract Signing'),
        ('evaluation', 'Property Evaluation'),
        ('follow_up', 'Follow-up Meeting'),
        ('virtual_tour', 'Virtual Tour'),
        ('other', 'Other'),
    ], string='Type', required=True, default='property_viewing', tracking=True)
    
    property_id = fields.Many2one(
        'real.estate.property',
        string='Related Property',
        help='Property related to this appointment'
    )
    
    lead_id = fields.Many2one(
        'real.estate.lead',
        string='Related Lead',
        help='Lead related to this appointment'
    )
    
    # Scheduling
    appointment_date = fields.Datetime(
        string='Appointment Date',
        required=True,
        tracking=True,
        help='Date and time of the appointment'
    )
    
    duration = fields.Float(
        string='Duration (Hours)',
        default=1.0,
        help='Expected duration in hours'
    )
    
    end_datetime = fields.Datetime(
        string='End Time',
        compute='_compute_end_datetime',
        store=True,
        help='Calculated end time'
    )
    
    # Location
    location_type = fields.Selection([
        ('property', 'At Property'),
        ('office', 'At Office'),
        ('client_location', 'At Client Location'),
        ('virtual', 'Virtual Meeting'),
        ('other', 'Other Location'),
    ], string='Location Type', default='property', required=True)
    
    location_address = fields.Text(
        string='Location Address',
        compute='_compute_location_address',
        store=True,
        help='Full address of the appointment location'
    )
    
    custom_location = fields.Char(
        string='Custom Location',
        help='Custom location if other is selected'
    )
    
    virtual_meeting_url = fields.Url(
        string='Meeting URL',
        help='Virtual meeting URL (Zoom, Teams, etc.)'
    )
    
    # Status and Management
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
        ('rescheduled', 'Rescheduled'),
    ], string='Status', default='draft', required=True, tracking=True)
    
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Very High'),
    ], string='Priority', default='1')
    
    # Confirmation and Reminders
    is_confirmed = fields.Boolean(
        string='Confirmed by Client',
        default=False,
        tracking=True
    )
    
    confirmation_date = fields.Datetime(
        string='Confirmation Date',
        readonly=True
    )
    
    reminder_sent = fields.Boolean(
        string='Reminder Sent',
        default=False
    )
    
    reminder_date = fields.Datetime(
        string='Reminder Sent Date'
    )
    
    # Description and Notes
    description = fields.Html(
        string='Description',
        help='Appointment description and agenda'
    )
    
    preparation_notes = fields.Text(
        string='Preparation Notes',
        help='Internal notes for appointment preparation'
    )
    
    meeting_notes = fields.Html(
        string='Meeting Notes',
        help='Notes taken during the meeting'
    )
    
    outcome = fields.Selection([
        ('interested', 'Client Interested'),
        ('not_interested', 'Not Interested'),
        ('needs_follow_up', 'Needs Follow-up'),
        ('ready_to_buy', 'Ready to Buy/Sell'),
        ('price_negotiation', 'Price Negotiation'),
        ('other', 'Other'),
    ], string='Outcome', help='Meeting outcome')
    
    # Follow-up
    follow_up_required = fields.Boolean(
        string='Follow-up Required',
        default=False
    )
    
    follow_up_date = fields.Date(
        string='Follow-up Date',
        help='Date for next follow-up'
    )
    
    follow_up_notes = fields.Text(
        string='Follow-up Notes',
        help='Notes for follow-up actions'
    )
    
    # Relations
    parent_appointment_id = fields.Many2one(
        'real.estate.appointment',
        string='Parent Appointment',
        help='Original appointment if this is a rescheduled one'
    )
    
    child_appointment_ids = fields.One2many(
        'real.estate.appointment',
        'parent_appointment_id',
        string='Rescheduled Appointments'
    )
    
    # Integration with Calendar
    calendar_event_id = fields.Many2one(
        'calendar.event',
        string='Calendar Event',
        help='Related calendar event'
    )
    
    # Documents and Attachments
    document_ids = fields.Many2many(
        'ir.attachment',
        'appointment_document_rel',
        'appointment_id',
        'attachment_id',
        string='Documents',
        help='Documents to bring or share during appointment'
    )
    
    # Computed Fields
    is_overdue = fields.Boolean(
        string='Overdue',
        compute='_compute_is_overdue',
        help='Whether appointment is overdue'
    )
    
    duration_display = fields.Char(
        string='Duration',
        compute='_compute_duration_display',
        help='Formatted duration display'
    )
    
    attendee_count = fields.Integer(
        string='Attendee Count',
        compute='_compute_attendee_count',
        help='Total number of attendees'
    )
    
    @api.depends('appointment_date', 'duration')
    def _compute_end_datetime(self):
        """Compute appointment end time"""
        for record in self:
            if record.appointment_date and record.duration:
                record.end_datetime = record.appointment_date + timedelta(hours=record.duration)
            else:
                record.end_datetime = False
    
    @api.depends('location_type', 'property_id', 'custom_location')
    def _compute_location_address(self):
        """Compute location address based on type"""
        for record in self:
            if record.location_type == 'property' and record.property_id:
                record.location_address = record.property_id.full_address
            elif record.location_type == 'office':
                # Get company address
                company = self.env.company
                address_parts = [
                    company.street or '',
                    company.street2 or '',
                    company.city or '',
                    company.state_id.name if company.state_id else '',
                    company.zip or '',
                    company.country_id.name if company.country_id else ''
                ]
                record.location_address = ', '.join(filter(None, address_parts))
            elif record.location_type == 'client_location' and record.client_id:
                # Get client address
                client = record.client_id
                address_parts = [
                    client.street or '',
                    client.street2 or '',
                    client.city or '',
                    client.state_id.name if client.state_id else '',
                    client.zip or '',
                    client.country_id.name if client.country_id else ''
                ]
                record.location_address = ', '.join(filter(None, address_parts))
            elif record.location_type == 'other':
                record.location_address = record.custom_location or ''
            elif record.location_type == 'virtual':
                record.location_address = record.virtual_meeting_url or 'Virtual Meeting'
            else:
                record.location_address = ''
    
    @api.depends('appointment_date', 'state')
    def _compute_is_overdue(self):
        """Check if appointment is overdue"""
        now = datetime.now()
        for record in self:
            record.is_overdue = (
                record.appointment_date and 
                record.appointment_date < now and 
                record.state in ['draft', 'confirmed']
            )
    
    @api.depends('duration')
    def _compute_duration_display(self):
        """Format duration for display"""
        for record in self:
            if record.duration:
                hours = int(record.duration)
                minutes = int((record.duration - hours) * 60)
                if minutes > 0:
                    record.duration_display = f"{hours}h {minutes}m"
                else:
                    record.duration_display = f"{hours}h"
            else:
                record.duration_display = ""
    
    @api.depends('additional_attendees')
    def _compute_attendee_count(self):
        """Compute total attendee count"""
        for record in self:
            # Agent + Client + Additional attendees
            record.attendee_count = 2 + len(record.additional_attendees)
    
    @api.model
    def create(self, vals):
        """Override create to generate sequence and create calendar event"""
        if vals.get('reference', _('New')) == _('New'):
            vals['reference'] = self.env['ir.sequence'].next_by_code('real.estate.appointment') or _('New')
        
        appointment = super().create(vals)
        appointment._create_calendar_event()
        return appointment
    
    def write(self, vals):
        """Override write to update calendar event"""
        result = super().write(vals)
        
        # Update calendar event if scheduling details changed
        if any(field in vals for field in ['appointment_date', 'duration', 'name', 'location_address']):
            for record in self:
                record._update_calendar_event()
        
        # Handle state changes
        if 'state' in vals:
            for record in self:
                record._handle_state_change(vals['state'])
        
        return result
    
    def _create_calendar_event(self):
        """Create calendar event for appointment"""
        self.ensure_one()
        
        if not self.appointment_date:
            return
        
        # Prepare attendee partners
        partner_ids = [self.client_id.id]
        if self.additional_attendees:
            partner_ids.extend(self.additional_attendees.ids)
        
        event_vals = {
            'name': self.name,
            'start': self.appointment_date,
            'stop': self.end_datetime or self.appointment_date,
            'location': self.location_address,
            'description': self.description,
            'user_id': self.agent_id.id,
            'partner_ids': [(6, 0, partner_ids)],
            'appointment_type_id': False,  # Default appointment type
        }
        
        calendar_event = self.env['calendar.event'].create(event_vals)
        self.calendar_event_id = calendar_event
    
    def _update_calendar_event(self):
        """Update existing calendar event"""
        self.ensure_one()
        
        if not self.calendar_event_id:
            self._create_calendar_event()
            return
        
        # Prepare attendee partners
        partner_ids = [self.client_id.id]
        if self.additional_attendees:
            partner_ids.extend(self.additional_attendees.ids)
        
        self.calendar_event_id.write({
            'name': self.name,
            'start': self.appointment_date,
            'stop': self.end_datetime or self.appointment_date,
            'location': self.location_address,
            'description': self.description,
            'partner_ids': [(6, 0, partner_ids)],
        })
    
    def _handle_state_change(self, new_state):
        """Handle appointment state changes"""
        self.ensure_one()
        
        if new_state == 'confirmed':
            self.is_confirmed = True
            self.confirmation_date = fields.Datetime.now()
            self.message_post(body=_('Appointment confirmed'))
            
        elif new_state == 'completed':
            self.message_post(body=_('Appointment completed'))
            # Create follow-up activity if required
            if self.follow_up_required and self.follow_up_date:
                self.activity_schedule(
                    'mail.mail_activity_data_call',
                    date_deadline=self.follow_up_date,
                    summary=f'Follow-up: {self.name}',
                    note=self.follow_up_notes or '',
                    user_id=self.agent_id.id,
                )
        
        elif new_state == 'cancelled':
            self.message_post(body=_('Appointment cancelled'))
            if self.calendar_event_id:
                self.calendar_event_id.active = False
    
    @api.constrains('appointment_date')
    def _check_appointment_date(self):
        """Validate appointment date"""
        for record in self:
            if record.appointment_date and record.appointment_date < datetime.now():
                if record.state == 'draft':
                    raise ValidationError(_('Cannot schedule appointments in the past'))
    
    @api.constrains('duration')
    def _check_duration(self):
        """Validate appointment duration"""
        for record in self:
            if record.duration <= 0:
                raise ValidationError(_('Appointment duration must be positive'))
            if record.duration > 24:
                raise ValidationError(_('Appointment duration cannot exceed 24 hours'))
    
    def action_confirm(self):
        """Confirm appointment"""
        for record in self:
            if record.state == 'draft':
                record.state = 'confirmed'
    
    def action_start(self):
        """Start appointment"""
        for record in self:
            if record.state == 'confirmed':
                record.state = 'in_progress'
    
    def action_complete(self):
        """Complete appointment"""
        for record in self:
            if record.state in ['confirmed', 'in_progress']:
                record.state = 'completed'
    
    def action_cancel(self):
        """Cancel appointment"""
        for record in self:
            if record.state not in ['completed', 'cancelled']:
                record.state = 'cancelled'
    
    def action_no_show(self):
        """Mark as no show"""
        for record in self:
            if record.state == 'confirmed':
                record.state = 'no_show'
    
    def action_reschedule(self):
        """Reschedule appointment"""
        self.ensure_one()
        
        # Create wizard for rescheduling
        return {
            'name': _('Reschedule Appointment'),
            'view_mode': 'form',
            'res_model': 'real.estate.appointment.reschedule.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_appointment_id': self.id,
                'default_new_date': self.appointment_date,
                'default_duration': self.duration,
            },
        }
    
    def send_reminder(self):
        """Send appointment reminder"""
        self.ensure_one()
        
        template = self.env.ref('real_estate_crm.email_template_appointment_reminder', False)
        if template and self.client_id.email:
            template.send_mail(self.id)
            self.reminder_sent = True
            self.reminder_date = fields.Datetime.now()
            self.message_post(body=_('Reminder sent to client'))
    
    @api.model
    def send_daily_reminders(self):
        """Cron job to send daily appointment reminders"""
        # Send reminders for appointments scheduled for tomorrow
        tomorrow = datetime.now() + timedelta(days=1)
        start_of_day = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = tomorrow.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        appointments = self.search([
            ('appointment_date', '>=', start_of_day),
            ('appointment_date', '<=', end_of_day),
            ('state', '=', 'confirmed'),
            ('reminder_sent', '=', False),
        ])
        
        for appointment in appointments:
            try:
                appointment.send_reminder()
            except Exception as e:
                _logger.error(f"Failed to send reminder for appointment {appointment.id}: {str(e)}")
    
    def action_view_calendar_event(self):
        """View related calendar event"""
        self.ensure_one()
        
        if not self.calendar_event_id:
            raise UserError(_('No calendar event found for this appointment'))
        
        return {
            'name': _('Calendar Event'),
            'view_mode': 'form',
            'res_model': 'calendar.event',
            'res_id': self.calendar_event_id.id,
            'type': 'ir.actions.act_window',
        }
    
    def get_google_calendar_url(self):
        """Generate Google Calendar URL for appointment"""
        self.ensure_one()
        
        if not self.appointment_date:
            return ''
        
        import urllib.parse
        from datetime import timezone
        
        # Convert to UTC for Google Calendar
        start_utc = self.appointment_date.replace(tzinfo=timezone.utc)
        end_utc = self.end_datetime.replace(tzinfo=timezone.utc) if self.end_datetime else start_utc
        
        params = {
            'action': 'TEMPLATE',
            'text': self.name,
            'dates': f"{start_utc.strftime('%Y%m%dT%H%M%SZ')}/{end_utc.strftime('%Y%m%dT%H%M%SZ')}",
            'location': self.location_address or '',
            'details': self.description or '',
        }
        
        base_url = 'https://calendar.google.com/calendar/render'
        return f"{base_url}?{urllib.parse.urlencode(params)}"