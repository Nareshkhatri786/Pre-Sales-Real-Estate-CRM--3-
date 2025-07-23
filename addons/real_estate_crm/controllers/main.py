# -*- coding: utf-8 -*-

from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal
import json
import logging

_logger = logging.getLogger(__name__)


class RealEstateController(http.Controller):
    """Main Real Estate CRM Controller"""
    
    @http.route('/real_estate/properties', type='http', auth='public', website=True)
    def property_list(self, **kwargs):
        """Public property listing page"""
        
        # Get search parameters
        search_term = kwargs.get('search', '')
        property_type = kwargs.get('type', '')
        min_price = kwargs.get('min_price', 0)
        max_price = kwargs.get('max_price', 0)
        bedrooms = kwargs.get('bedrooms', 0)
        location = kwargs.get('location', '')
        
        # Build domain for property search
        domain = [('state', '=', 'available')]
        
        if search_term:
            domain.append(('name', 'ilike', search_term))
        
        if property_type:
            domain.append(('property_type_id', '=', int(property_type)))
        
        if min_price:
            domain.append(('expected_price', '>=', float(min_price)))
        
        if max_price:
            domain.append(('expected_price', '<=', float(max_price)))
        
        if bedrooms:
            domain.append(('bedrooms', '>=', int(bedrooms)))
        
        if location:
            domain.extend([
                '|', '|',
                ('city', 'ilike', location),
                ('state_id.name', 'ilike', location),
                ('country_id.name', 'ilike', location)
            ])
        
        # Get properties
        properties = request.env['real.estate.property'].sudo().search(domain, limit=20)
        
        # Get property types for filter
        property_types = request.env['real.estate.property.type'].sudo().search([('active', '=', True)])
        
        values = {
            'properties': properties,
            'property_types': property_types,
            'search_term': search_term,
            'selected_type': property_type,
            'min_price': min_price,
            'max_price': max_price,
            'bedrooms': bedrooms,
            'location': location,
            'page_name': 'property_list',
        }
        
        return request.render('real_estate_crm.property_list_template', values)
    
    @http.route('/real_estate/property/<int:property_id>', type='http', auth='public', website=True)
    def property_detail(self, property_id, **kwargs):
        """Property detail page"""
        
        property_obj = request.env['real.estate.property'].sudo().browse(property_id)
        
        if not property_obj.exists() or property_obj.state != 'available':
            return request.not_found()
        
        # Get similar properties
        similar_domain = [
            ('state', '=', 'available'),
            ('property_type_id', '=', property_obj.property_type_id.id),
            ('id', '!=', property_id)
        ]
        
        similar_properties = request.env['real.estate.property'].sudo().search(
            similar_domain, limit=4
        )
        
        values = {
            'property': property_obj,
            'similar_properties': similar_properties,
            'page_name': 'property_detail',
        }
        
        return request.render('real_estate_crm.property_detail_template', values)
    
    @http.route('/real_estate/inquiry', type='http', auth='public', website=True, methods=['POST'])
    def property_inquiry(self, **kwargs):
        """Handle property inquiry form"""
        
        property_id = kwargs.get('property_id')
        name = kwargs.get('name')
        email = kwargs.get('email')
        phone = kwargs.get('phone')
        message = kwargs.get('message')
        
        if not all([property_id, name, email, message]):
            return json.dumps({'error': 'Missing required fields'})
        
        try:
            # Create lead
            lead_vals = {
                'name': f'Inquiry for Property #{property_id}',
                'partner_name': name,
                'email_from': email,
                'phone': phone,
                'description': message,
                'interested_property_id': int(property_id),
                'lead_type': 'buyer',
                'source_id': request.env.ref('utm.utm_source_website').id,
            }
            
            lead = request.env['real.estate.lead'].sudo().create(lead_vals)
            
            # Send notification email to agent
            property_obj = request.env['real.estate.property'].sudo().browse(int(property_id))
            if property_obj.salesperson_id:
                # Send email notification
                template = request.env.ref('real_estate_crm.email_template_new_inquiry', False)
                if template:
                    template.sudo().send_mail(lead.id)
            
            return json.dumps({'success': True, 'message': 'Thank you for your inquiry! We will contact you soon.'})
            
        except Exception as e:
            _logger.error(f"Error creating property inquiry: {str(e)}")
            return json.dumps({'error': 'Failed to submit inquiry. Please try again.'})
    
    @http.route('/real_estate/agent/<int:agent_id>', type='http', auth='public', website=True)
    def agent_profile(self, agent_id, **kwargs):
        """Agent profile page"""
        
        agent = request.env['real.estate.agent'].sudo().browse(agent_id)
        
        if not agent.exists() or agent.status != 'active':
            return request.not_found()
        
        # Get agent's active properties
        agent_properties = request.env['real.estate.property'].sudo().search([
            ('salesperson_id', '=', agent.user_id.id),
            ('state', 'in', ['available', 'offer_received'])
        ], limit=12)
        
        values = {
            'agent': agent,
            'agent_properties': agent_properties,
            'page_name': 'agent_profile',
        }
        
        return request.render('real_estate_crm.agent_profile_template', values)
    
    @http.route('/real_estate/search_ajax', type='json', auth='public', website=True)
    def search_properties_ajax(self, **kwargs):
        """AJAX property search"""
        
        search_params = kwargs
        domain = [('state', '=', 'available')]
        
        # Apply filters
        if search_params.get('search'):
            domain.append(('name', 'ilike', search_params['search']))
        
        if search_params.get('property_type'):
            domain.append(('property_type_id', '=', int(search_params['property_type'])))
        
        if search_params.get('min_price'):
            domain.append(('expected_price', '>=', float(search_params['min_price'])))
        
        if search_params.get('max_price'):
            domain.append(('expected_price', '<=', float(search_params['max_price'])))
        
        if search_params.get('bedrooms'):
            domain.append(('bedrooms', '>=', int(search_params['bedrooms'])))
        
        # Search properties
        properties = request.env['real.estate.property'].sudo().search(domain, limit=20)
        
        # Format results
        results = []
        for prop in properties:
            results.append({
                'id': prop.id,
                'name': prop.name,
                'price': prop.expected_price,
                'currency': prop.currency_id.symbol,
                'bedrooms': prop.bedrooms,
                'bathrooms': prop.bathrooms,
                'area': prop.living_area or prop.total_area,
                'location': prop.city,
                'image_url': f'/web/image/real.estate.property/{prop.id}/image_1920' if prop.image_1920 else '/real_estate_crm/static/src/img/property-placeholder.jpg',
                'url': f'/real_estate/property/{prop.id}',
            })
        
        return {'properties': results, 'count': len(results)}


class RealEstatePortal(CustomerPortal):
    """Portal extension for Real Estate CRM"""
    
    def _prepare_home_portal_values(self, **kwargs):
        """Add real estate data to portal homepage"""
        values = super()._prepare_home_portal_values(**kwargs)
        partner = request.env.user.partner_id
        
        if partner.is_real_estate_client:
            # Add client-specific data
            values.update({
                'property_count': request.env['real.estate.property'].search_count([
                    '|',
                    ('buyer_id', '=', partner.id),
                    ('seller_id', '=', partner.id)
                ]),
                'lead_count': request.env['real.estate.lead'].search_count([
                    ('partner_id', '=', partner.id)
                ]),
                'appointment_count': request.env['real.estate.appointment'].search_count([
                    ('client_id', '=', partner.id)
                ]),
            })
        
        return values
    
    @http.route(['/my/properties', '/my/properties/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_properties(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        """Portal page for client properties"""
        
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        
        # Get properties related to this client
        domain = [
            '|',
            ('buyer_id', '=', partner.id),
            ('seller_id', '=', partner.id)
        ]
        
        searchbar_sortings = {
            'date': {'label': _('Date'), 'order': 'create_date desc'},
            'name': {'label': _('Name'), 'order': 'name'},
            'price': {'label': _('Price'), 'order': 'expected_price desc'},
        }
        
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']
        
        # Count properties
        property_count = request.env['real.estate.property'].search_count(domain)
        
        # Pager
        pager = request.website.pager(
            url="/my/properties",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=property_count,
            page=page,
            step=self._items_per_page
        )
        
        # Get properties
        properties = request.env['real.estate.property'].search(
            domain, order=order, limit=self._items_per_page, offset=pager['offset']
        )
        
        values.update({
            'date': date_begin,
            'properties': properties,
            'page_name': 'property',
            'pager': pager,
            'default_url': '/my/properties',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        
        return request.render("real_estate_crm.portal_my_properties", values)
    
    @http.route(['/my/appointments', '/my/appointments/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_appointments(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        """Portal page for client appointments"""
        
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        
        domain = [('client_id', '=', partner.id)]
        
        searchbar_sortings = {
            'date': {'label': _('Date'), 'order': 'appointment_date desc'},
            'name': {'label': _('Subject'), 'order': 'name'},
            'state': {'label': _('Status'), 'order': 'state'},
        }
        
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']
        
        # Count appointments
        appointment_count = request.env['real.estate.appointment'].search_count(domain)
        
        # Pager
        pager = request.website.pager(
            url="/my/appointments",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=appointment_count,
            page=page,
            step=self._items_per_page
        )
        
        # Get appointments
        appointments = request.env['real.estate.appointment'].search(
            domain, order=order, limit=self._items_per_page, offset=pager['offset']
        )
        
        values.update({
            'date': date_begin,
            'appointments': appointments,
            'page_name': 'appointment',
            'pager': pager,
            'default_url': '/my/appointments',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        
        return request.render("real_estate_crm.portal_my_appointments", values)
    
    @http.route(['/my/property/<int:property_id>'], type='http', auth="user", website=True)
    def portal_property_detail(self, property_id, **kw):
        """Portal property detail page"""
        
        partner = request.env.user.partner_id
        property_obj = request.env['real.estate.property'].search([
            ('id', '=', property_id),
            '|',
            ('buyer_id', '=', partner.id),
            ('seller_id', '=', partner.id)
        ])
        
        if not property_obj:
            return request.not_found()
        
        values = {
            'property': property_obj,
            'page_name': 'property_detail',
        }
        
        return request.render("real_estate_crm.portal_property_detail", values)