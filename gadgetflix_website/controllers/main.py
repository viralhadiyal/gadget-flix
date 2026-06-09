# -*- coding: utf-8 -*-

from odoo.addons.website_sale.controllers.main import WebsiteSale, TableCompute
from odoo.addons.website_sale.controllers.delivery import Delivery
import itertools
import json
from datetime import datetime
from werkzeug.exceptions import Forbidden, NotFound
from werkzeug.urls import url_decode, url_encode, url_parse
from odoo.fields import Command, Domain
from odoo import http, fields, tools
from odoo.http import request, route
from odoo.tools import SQL, clean_context, float_round, groupby, lazy, str2bool
from odoo.tools.translate import LazyTranslate, _
from odoo.addons.payment import utils as payment_utils
from odoo.addons.payment.controllers import portal as payment_portal
from odoo.addons.sale.controllers import portal as sale_portal
from odoo.addons.html_editor.tools import get_video_thumbnail
from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.website.models.ir_http import sitemap_qs2dom
from odoo.addons.website_sale.const import SHOP_PATH
from odoo.addons.website_sale.models.website import (
    PRICELIST_SELECTED_SESSION_CACHE_KEY,
    PRICELIST_SESSION_CACHE_KEY,
)

_lt = LazyTranslate(__name__)


class WebsiteSaleShop(Delivery):
    # =========================================================
    # 2-Step Checkout Override
    # Step 1 → /shop/cart   (Order Summary)
    # Step 2 → /shop/checkout  (Address + Delivery + Payment)
    #
    # Delivery method options:
    #   • COD     – Cash on Delivery
    #   • Prepaid – Prepaid (paid online via payment provider)
    # =========================================================

    @route(
        '/shop/checkout', type='http', methods=['GET'], auth='public', website=True, sitemap=False, list_as_website_content=_lt("Shop Checkout")
    )
    def shop_checkout(self, try_skip_step=None, **query_params):
        """Override: combine address/delivery + payment onto /shop/checkout."""
        try_skip_step = str2bool(try_skip_step or 'false')
        order_sudo = request.cart
        request.session['sale_last_order_id'] = order_sudo.id

        if redirection := self._check_cart_and_addresses(order_sudo):
            return redirection

        checkout_page_values = self._prepare_checkout_page_values(order_sudo, **query_params)

        can_skip_delivery = True
        if order_sudo._has_deliverable_products():
            can_skip_delivery = False
            available_dms = order_sudo._get_delivery_methods()
            checkout_page_values['delivery_methods'] = available_dms
            if delivery_method := order_sudo._get_preferred_delivery_method(available_dms):
                rate = delivery_method.rate_shipment(order_sudo)
                if (
                    not order_sudo.carrier_id
                    or not rate.get('success')
                    or order_sudo.amount_delivery != rate['price']
                ):
                    order_sudo._set_delivery_method(delivery_method, rate=rate)

        # Find COD and Prepaid carriers dynamically
        Carrier = request.env['delivery.carrier'].sudo()
        cod_carrier = Carrier.search([('allow_cash_on_delivery', '=', True), ('is_published', '=', True)], limit=1)
        prepaid_carrier = Carrier.search([('allow_cash_on_delivery', '=', False), ('is_published', '=', True)], limit=1)

        checkout_page_values['gf_cod_carrier_id'] = cod_carrier.id
        checkout_page_values['gf_prepaid_carrier_id'] = prepaid_carrier.id

        # Merge payment form values so the payment widget renders inline
        order_sudo._recompute_cart()
        request.update_context(gf_show_all_payment_methods=True)
        payment_values = self._get_shop_payment_values(order_sudo, **query_params)
        checkout_page_values.update(payment_values)
        checkout_page_values['gf_combined_checkout'] = True  # flag for template
        checkout_page_values['display_submit_button'] = True  # Force inline submit button to show

        checkout_page_values.update(request.website._get_checkout_step_values())

        if try_skip_step and can_skip_delivery:
            return request.redirect(checkout_page_values['next_website_checkout_step_href'])

        return request.render('website_sale.checkout', checkout_page_values)


    @route('/shop/payment', type='http', auth='public', website=True, sitemap=False)
    def shop_payment(self, **post):
        """Redirect /shop/payment back to the combined checkout page."""
        return request.redirect('/shop/checkout')

    @route('/shop/cart/mini', type='http', auth="public", website=True, sitemap=False)
    def cart_mini(self, **post):
        order = request.cart
        if order and order.state != 'draft':
            request.session['sale_order_id'] = None
            order = request.cart
        values = {
            'website_sale_order': order,
            'date': fields.Date.today(),
            'suggested_products': [],
        }
        if order:
            order._update_programs_and_rewards()
            order._auto_apply_rewards()
            values['suggested_products'] = order._cart_accessories()
        return request.render("gadgetflix_website.cart_offcanvas_content", values)

    def _order_summary_values(self, order, **kwargs):
        """Extend to include raw float value for frontend JS update."""
        values = super()._order_summary_values(order, **kwargs)
        values['amount_total_raw'] = order.amount_total
        return values


    def _get_available_attribute_value_ids(
        self, search, category, attribute_value_dict, attributes
    ):
        ProductTemplate = request.env['product.template']
        AttributeLine = request.env['product.template.attribute.line']

        available_value_ids_by_attribute = {}
        available_value_ids = set()

        for attribute in attributes:
            other_attribute_values = {
                attribute_id: value_ids
                for attribute_id, value_ids in attribute_value_dict.items()
                if attribute_id != attribute.id
            }
            product_query = ProductTemplate._search(
                self._get_shop_domain(search, category, other_attribute_values)
            )
            value_ids = AttributeLine.search([
                ('product_tmpl_id', 'in', product_query),
                ('attribute_id', '=', attribute.id),
                ('attribute_id.visibility', '=', 'visible'),
            ]).value_ids.ids
            available_value_ids_by_attribute[attribute.id] = value_ids
            available_value_ids.update(value_ids)

        return available_value_ids_by_attribute, list(available_value_ids)

    def _get_gadgetflix_page_values(self, domain=None, limit=12):
        website = request.website
        product_domain = Domain(website.sale_product_domain())
        if domain:
            product_domain &= Domain(domain)

        Product = request.env['product.template'].sudo()
        Category = request.env['product.public.category'].sudo()

        products = Product.search(product_domain, limit=limit, order='website_sequence asc, id desc')
        featured_products = Product.search(
            product_domain & Domain('gadgetflix_show_featured_home', '=', True),
            limit=12,
            order='website_sequence asc, id desc',
        )
        new_arrival_products = Product.search(
            product_domain & Domain('gadgetflix_show_new_arrival_home', '=', True),
            limit=12,
            order='website_sequence asc, id desc',
        )
        anti_yellow_products = Product.search(
            product_domain & Domain('gadgetflix_show_anti_yellow', '=', True),
            limit=12,
            order='website_sequence asc, id desc',
        )
        anti_yellow_best_selling_products = Product.search(
            product_domain & Domain('gadgetflix_show_anti_yellow_best_selling', '=', True),
            limit=12,
            order='website_sequence asc, id desc',
        )
        about_products = Product.search(
            product_domain & Domain('gadgetflix_show_about_page', '=', True),
            limit=12,
            order='website_sequence asc, id desc',
        )
        priced_products = (
            products
            | featured_products
            | new_arrival_products
            | anti_yellow_products
            | anti_yellow_best_selling_products
            | about_products
        )
        category_domain = (
            Domain('parent_id', '=', False)
            & Domain(website.website_domain())
            & Domain('has_published_products', '=', True)
            & Domain('gadgetflix_show_home', '=', True)
        )
        return {
            'website_categories': Category.search(category_domain, limit=6),
            'featured_products': featured_products,
            'new_arrival_products': new_arrival_products,
            'anti_yellow_products': anti_yellow_products,
            'anti_yellow_best_selling_products': anti_yellow_best_selling_products,
            'about_products': about_products,
            'products': products,
            'product_prices': priced_products._get_sales_prices(website) if priced_products else {},
        }

    @route('/', type='http', auth='public', website=True, sitemap=True)
    def gadgetflix_homepage(self, **kwargs):
        values = self._get_gadgetflix_page_values(limit=12)
        values['products'] = values['anti_yellow_products']
        return request.render('gadgetflix_website.anti_yellow_cases', values)

    @route('/home', type='http', auth='public', website=True, sitemap=True)
    def gadgetflix_home(self, **kwargs):
        values = self._get_gadgetflix_page_values(limit=12)
        return request.render('gadgetflix_website.homepage', values)

    @route('/about', type='http', auth='public', website=True, sitemap=True)
    def gadgetflix_about(self, **kwargs):
        return request.render('gadgetflix_website.about_page', self._get_gadgetflix_page_values(limit=8))

    @route('/faq', type='http', auth='public', website=True, sitemap=False)
    def gadgetflix_faq(self, **kwargs):
        return request.redirect('/contact')

    @route('/contact', type='http', auth='public', website=True, sitemap=True)
    def gadgetflix_contact(self, **kwargs):
        return request.render('gadgetflix_website.contact_page', self._get_gadgetflix_page_values(limit=4))

    @route(['/anti-yellow-cases', '/anti-yellow'], type='http', auth='public', website=True, sitemap=True)
    def gadgetflix_anti_yellow_cases(self, **kwargs):
        values = self._get_gadgetflix_page_values(limit=12)
        values['products'] = values['anti_yellow_products']
        return request.render('gadgetflix_website.anti_yellow_cases', values)

    @route('/gadgetflix/cart/preview', type='http', auth='public', website=True, sitemap=False)
    def gadgetflix_cart_preview(self, **kwargs):
        order = request.cart
        currency = request.website.currency_id

        def format_amount(amount):
            value = f"{amount:,.2f}"
            if currency.position == 'after':
                return f"{value} {currency.symbol}"
            return f"{currency.symbol} {value}"

        lines = []
        if order:
            cart_lines = order.order_line.filtered(
                lambda line: not line.display_type and line.product_id and line.product_uom_qty
            )
            for line in cart_lines:
                product = line.product_id
                template = product.product_tmpl_id
                lines.append({
                    'name': product.display_name,
                    'quantity': line.product_uom_qty,
                    'price': format_amount(line.price_total),
                    'image_url': f'/web/image/product.product/{product.id}/image_128',
                    'url': template.website_url or '/shop/cart',
                })

        payload = {
            'quantity': order.cart_quantity if order else 0,
            'total': format_amount(order.amount_total if order else 0),
            'lines': lines,
        }
        return request.make_response(
            json.dumps(payload),
            headers=[('Content-Type', 'application/json')],
        )

    @route('/accessories', type='http', auth='public', website=True, sitemap=True)
    def gadgetflix_accessories(self, **kwargs):
        return request.redirect('/shop?search=Accessories')

    @route('/llms.txt', type='http', auth='public', website=True, sitemap=False)
    def gadgetflix_llms_txt(self, **kwargs):
        content = (request.website.sudo().gadgetflix_llms_txt_content or '').strip()
        if not content:
            raise NotFound()

        body = content if content.endswith('\n') else f'{content}\n'
        return request.make_response(
            body,
            headers=[
                ('Content-Type', 'text/plain; charset=utf-8'),
                ('Cache-Control', 'public, max-age=3600'),
            ],
        )

    @route(
        [
            SHOP_PATH,
            f'{SHOP_PATH}/page/<int:page>',
            f'{SHOP_PATH}/category/<model("product.public.category"):category>',
            f'{SHOP_PATH}/category/<model("product.public.category"):category>/page/<int:page>',
        ],
        type='http',
        auth='public',
        website=True,
        list_as_website_content=_lt("Shop"),
        sitemap=WebsiteSale.sitemap_shop,
        # Sends a 404 error in case of any Access error instead of 403.
        handle_params_access_error=lambda e, **kwargs: NotFound.code,
    )
    def shop(self, page=0, category=None, search='', min_price=0.0, max_price=0.0, tags='', **post):
        if not request.website.has_ecommerce_access():
            return request.redirect(f'/web/login?redirect={request.httprequest.path}')

        is_category_in_query = category and isinstance(category, str)
        category = self._validate_and_get_category(category)

        if is_category_in_query:
            query = self._get_filtered_query_string(
                request.httprequest.query_string.decode(), keys_to_remove=['category']
            )
            return request.redirect(f'{self._get_shop_path(category, page)}?{query}', code=301)

        try:
            min_price = float(min_price)
        except ValueError:
            min_price = 0

        try:
            max_price = float(max_price)
        except ValueError:
            max_price = 0

        website = request.env['website'].get_current_website()
        website_domain = website.website_domain()

        ppg = website.shop_ppg or 21
        ppr = website.shop_ppr or 4
        gap = website.shop_gap or "16px"

        request_args = request.httprequest.args
        attribute_values = request_args.getlist('attribute_values')
        attribute_value_dict = self._get_attribute_value_dict(attribute_values)

        attribute_ids = set(attribute_value_dict.keys())
        attribute_value_ids = set(itertools.chain.from_iterable(attribute_value_dict.values()))

        if attribute_values:
            request.session['attribute_values'] = attribute_values
            post['attribute_values'] = attribute_values
        else:
            request.session.pop('attribute_values', None)

        filter_by_tags_enabled = website.is_view_active('website_sale.filter_products_tags')
        if filter_by_tags_enabled:
            if tags:
                post['tags'] = tags
                tags = {self.env['ir.http']._unslug(tag)[1] for tag in tags.split(',')}
            else:
                post['tags'] = None
                tags = {}

        url = self._get_shop_path(category)
        keep = QueryURL(
            url, **self._shop_get_query_url_kwargs(search, min_price, max_price, **post)
        )

        now = datetime.timestamp(datetime.now())
        if 'website_sale_pricelist_time' in request.session:
            pricelist_save_time = request.session['website_sale_pricelist_time']
            if pricelist_save_time < now - 60 * 60:
                request.session.pop(PRICELIST_SESSION_CACHE_KEY, None)
                request.session['website_sale_pricelist_time'] = now

        filter_by_price_enabled = website.is_view_active('website_sale.filter_products_price')
        if filter_by_price_enabled:
            company_currency = website.company_id.sudo().currency_id
            conversion_rate = request.env['res.currency']._get_conversion_rate(
                company_currency,
                website.currency_id,
                request.website.company_id,
                fields.Date.today()
            )
        else:
            conversion_rate = 1

        if search:
            post['search'] = search

        options = self._get_search_options(
            category=category,
            attribute_value_dict=attribute_value_dict,
            min_price=min_price,
            max_price=max_price,
            conversion_rate=conversion_rate,
            display_currency=website.currency_id,
            **post
        )

        fuzzy_search_term, product_count, search_product = self._shop_lookup_products(
            options, post, search, website
        )

        if filter_by_price_enabled:
            Product = request.env['product.template'].with_context(bin_size=True)
            search_term = fuzzy_search_term if fuzzy_search_term else search
            domain = self._get_shop_domain(search_term, category, attribute_value_dict)

            query = Product._search(domain)
            sql = query.select(
                SQL(
                    "COALESCE(MIN(list_price), 0) * %(conversion_rate)s, "
                    "COALESCE(MAX(list_price), 0) * %(conversion_rate)s",
                    conversion_rate=conversion_rate,
                )
            )
            available_min_price, available_max_price = request.env.execute_query(sql)[0]

            if min_price or max_price:
                if min_price:
                    min_price = min_price if min_price <= available_max_price else available_min_price
                    post['min_price'] = min_price
                if max_price:
                    max_price = max_price if max_price >= available_min_price else available_max_price
                    post['max_price'] = max_price

        ProductTag = request.env['product.tag']
        if filter_by_tags_enabled and search_product:
            all_tags = ProductTag.search_fetch(Domain.AND([
                Domain('visible_to_customers', '=', True),
                Domain.OR([
                    Domain('product_template_ids.is_published', '=', True),
                    Domain('product_ids.is_published', '=', True),
                ]),
                website_domain,
            ]))
        else:
            all_tags = ProductTag

        Category = request.env['product.public.category']
        categs_domain = Domain('parent_id', '=', False) & website_domain

        if search:
            search_categories = Category.search(
                Domain('product_tmpl_ids', 'in', search_product.ids) & website_domain
            ).parents_and_self
            categs_domain &= Domain('id', 'in', search_categories.ids)
        else:
            search_categories = Category

        categs = Category.search_fetch(categs_domain)

        category_entries = Category
        if category:
            category_entries = not search and category.child_id or category.child_id.filtered(
                lambda c: c.id in search_categories.ids
            )
            if not category_entries:
                parent = category.parent_id
                category_entries = not search and parent.child_id or parent.child_id.filtered(
                    lambda c: c.id in search_categories.ids
                )
            if not search and not request.env.user._is_internal():
                category_entries = category_entries.filtered("has_published_products")
        else:
            category_entries = categs

        pager = website.pager(
            url=url,
            total=product_count,
            page=page,
            step=ppg,
            scope=5,
            url_args=post
        )
        offset = pager['offset']
        products = search_product[offset:offset + ppg]
        products.fetch()

        variants = request.env['product.product'].sudo().browse(
            product._get_first_possible_variant_id() for product in products
        )
        variants.fetch()
        product_variants = dict(zip(products, variants))

        search_term = fuzzy_search_term if fuzzy_search_term else search

        ProductAttribute = request.env['product.attribute']
        if products:
            product_query = request.env['product.template']._search(
                self._get_shop_domain(search_term, category, attribute_value_dict)
            )
            attributes_grouped = request.env['product.template.attribute.line']._read_group(
                domain=[
                    ('product_tmpl_id', 'in', product_query),
                    ('attribute_id.visibility', '=', 'visible'),
                ],
                groupby=['attribute_id'],
                order='attribute_id'
            )
            attribute_ids = [attribute.id for attribute, in attributes_grouped]
            attributes = ProductAttribute.browse(attribute_ids)
        else:
            attributes = ProductAttribute.browse(attribute_ids).sorted()

        if website.is_view_active('website_sale.products_list_view'):
            layout_mode = 'list'
        else:
            layout_mode = 'grid'

        products_prices = products._get_sales_prices(website)
        product_query_params = self._get_product_query_params(**post)

        available_value_ids_by_attribute, available_value_ids = (
            self._get_available_attribute_value_ids(
                search_term, category, attribute_value_dict, attributes
            )
        )
        available_value_ids_set = set(available_value_ids)
        attributes = attributes.filtered(
            lambda attribute: len(available_value_ids_by_attribute.get(attribute.id, [])) > 1
            or bool(
                set(attribute_value_dict.get(attribute.id, []))
                & available_value_ids_set
            )
        )

        selected_values = request.env['product.attribute.value'].browse(
            list(attribute_value_ids)
        )

        grouped_attributes_values = selected_values.sorted().grouped('attribute_id')

        values = {
            'auto_assign_ribbons': self.env['product.ribbon'].sudo().search([('assign', '!=', 'manual')]),
            'search': fuzzy_search_term or search,
            'original_search': fuzzy_search_term and search,
            'order': post.get('order', ''),
            'category': category,
            'attrib_values': attribute_value_dict,
            'attrib_set': attribute_value_ids,
            'pager': pager,
            'products': products,
            'product_variants': product_variants,
            'search_product': search_product,
            'search_count': product_count,
            'bins': TableCompute().process(products, ppg, ppr),
            'ppg': ppg,
            'ppr': ppr,
            'gap': gap,
            'categories': categs,
            'category_entries': category_entries,
            'attributes': attributes,
            'available_value_ids': available_value_ids,
            'available_value_ids_by_attribute': available_value_ids_by_attribute,
            'keep': keep,
            'search_categories_ids': search_categories.ids,
            'layout_mode': layout_mode,
            'get_product_prices': lambda product: products_prices[product.id],
            'float_round': float_round,
            'shop_path': SHOP_PATH,
            'product_query_params': product_query_params,
            'grouped_attributes_values': grouped_attributes_values,
            'previewed_attribute_values': lazy(
                lambda: products._get_previewed_attribute_values(category, product_query_params),
            ),
        }

        if filter_by_price_enabled:
            values['min_price'] = min_price or available_min_price
            values['max_price'] = max_price or available_max_price
            values['available_min_price'] = float_round(available_min_price, 2)
            values['available_max_price'] = float_round(available_max_price, 2)

        if filter_by_tags_enabled:
            values.update({'all_tags': all_tags, 'tags': tags})

        if category:
            values['main_object'] = category

        values.update(self._get_additional_shop_values(values, **post))
        return request.render("website_sale.products", values)

    @route('/gadgetflix/cart/apply_promo', type='http', auth='public', methods=['GET', 'POST'], csrf=False, website=True)
    def apply_promo(self, **kwargs):
        is_json = request.httprequest.headers.get('Content-Type') == 'application/json' or request.httprequest.is_json
        if not is_json:
            return request.redirect('/shop/checkout')

        try:
            data = json.loads(request.httprequest.data.decode('utf-8'))
            params = data.get('params', {})
        except Exception:
            params = {}

        promo = params.get('promo', '').strip()
        order_sudo = request.cart
        if not order_sudo:
            payload = {'result': {'success': False, 'error': _("No active cart found.")}}
            return request.make_response(json.dumps(payload), headers=[('Content-Type', 'application/json')])

        if not promo:
            payload = {'result': {'success': False, 'error': _("Please enter a valid promo code.")}}
            return request.make_response(json.dumps(payload), headers=[('Content-Type', 'application/json')])

        coupon_status = order_sudo._try_apply_code(promo)
        if coupon_status.get('not_found'):
            pricelist_sudo = request.env['product.pricelist'].sudo().search([('code', '=', promo)], limit=1)
            if pricelist_sudo and request.website.is_pricelist_available(pricelist_sudo.id):
                order_sudo._apply_pricelist(pricelist=pricelist_sudo)
                payload = {'result': {'success': True}}
                return request.make_response(json.dumps(payload), headers=[('Content-Type', 'application/json')])
            else:
                payload = {'result': {'success': False, 'error': _("Invalid or expired promo code.")}}
                return request.make_response(json.dumps(payload), headers=[('Content-Type', 'application/json')])
        elif coupon_status.get('error'):
            payload = {'result': {'success': False, 'error': coupon_status['error']}}
            return request.make_response(json.dumps(payload), headers=[('Content-Type', 'application/json')])

        if len(coupon_status) == 1:
            coupon, rewards = next(iter(coupon_status.items()))
            if len(rewards) == 1:
                reward = rewards
            else:
                reward = rewards[0]
            if reward and (not reward.multi_product or request.env.context.get('product_id')):
                try:
                    reward_status = order_sudo._apply_program_reward(reward, coupon)
                    if 'error' in reward_status:
                        payload = {'result': {'success': False, 'error': reward_status['error']}}
                        return request.make_response(json.dumps(payload), headers=[('Content-Type', 'application/json')])
                except Exception as e:
                    payload = {'result': {'success': False, 'error': str(e)}}
                    return request.make_response(json.dumps(payload), headers=[('Content-Type', 'application/json')])

                order_sudo._update_programs_and_rewards()
                if order_sudo.carrier_id.free_over and not reward.program_id.is_payment_program:
                    res = order_sudo.carrier_id.rate_shipment(order_sudo)
                    if res.get('success'):
                        order_sudo.set_delivery_line(order_sudo.carrier_id, res['price'])
                    else:
                        order_sudo._remove_delivery_line()

        payload = {'result': {'success': True}}
        return request.make_response(json.dumps(payload), headers=[('Content-Type', 'application/json')])

    @route('/gadgetflix/cart/summary_html', type='http', auth='public', methods=['GET', 'POST'], csrf=False, website=True)
    def cart_summary_html(self, **kwargs):
        is_json = request.httprequest.headers.get('Content-Type') == 'application/json' or request.httprequest.is_json
        if not is_json:
            return request.redirect('/shop/checkout')

        order_sudo = request.cart
        if not order_sudo:
            payload = {'result': {'success': False, 'cart_summary_content': '', 'total': ''}}
            return request.make_response(json.dumps(payload), headers=[('Content-Type', 'application/json')])

        values = {
            'website_sale_order': order_sudo,
            'date': fields.Date.today(),
            'suggested_products': [],
        }
        values.update(request.website._get_checkout_step_values())
        
        cart_summary_content = request.env['ir.ui.view']._render_template('website_sale.cart_summary_content', values)
        total_content = request.env['ir.ui.view']._render_template('website_sale.total', values)
        
        payload = {
            'result': {
                'success': True,
                'cart_summary_content': cart_summary_content.decode('utf-8') if isinstance(cart_summary_content, bytes) else cart_summary_content,
                'total': total_content.decode('utf-8') if isinstance(total_content, bytes) else total_content,
            }
        }
        return request.make_response(json.dumps(payload), headers=[('Content-Type', 'application/json')])


class AntiYellowController(http.Controller):

    @http.route('/anti-yellow-case', type='http', auth='public', website=True, sitemap=True)
    def anti_yellow_case_page(self, **kw):
        """Premium single landing page for Anti-Yellow Clear Cases.
        Finds all anti-yellow products and extracts their brand/model structure
        so the frontend can drive a fully dynamic Brand → Model → Add to Cart flow.
        """
        website = request.website
        Product = request.env['product.template'].sudo()

        # Find the anti-yellow category by name
        ay_category = request.env['product.public.category'].sudo().search([
            ('name', 'ilike', 'Desks')
        ], limit=1)
        # Fetch all published products in that category
        domain = [('website_published', '=', True)]
        if ay_category:
            domain.append(('public_categ_ids', 'in', ay_category.ids))

        anti_yellow_products = Product.search(
            domain + website.website_domain(),
            order='website_sequence asc, id asc'
        )


        # Build brand list: [{brand_value_id, brand_name, product_id, product_name,
        #                      first_variant_id, first_price, first_image_url}, ...]
        brands = []
        seen_brand_ids = set()

        for product in anti_yellow_products:
            brand_line = product.attribute_line_ids.filtered(
                lambda l: l.attribute_id.name.lower() == 'brand'
            )[:1]
            if not brand_line:
                continue
            brand_value = brand_line.product_template_value_ids._only_active()[:1]
            if not brand_value:
                brand_value = brand_line.value_ids[:1]
            if not brand_value or brand_value.id in seen_brand_ids:
                continue
            seen_brand_ids.add(brand_value.id)

            # Get first available variant for initial price/image display
            first_variant = product.product_variant_ids[:1]

            brands.append({
                'brand_value_id': brand_value.product_attribute_value_id.id if hasattr(brand_value, 'product_attribute_value_id') else brand_value.id,
                'brand_name': brand_value.name,
                'product_id': product.id,
                'product_name': product.name,
                'first_variant_id': first_variant.id if first_variant else 0,
                'first_price': first_variant.lst_price if first_variant else product.list_price,
                'first_image_url': f'/web/image/product.template/{product.id}/image_512',
            })

        # Default selection: first brand
        default_brand = brands[0] if brands else None

        default_product = request.env['product.template'].sudo().browse(default_brand['product_id']) if default_brand else None

        return request.render('gadgetflix_website.anti_yellow_case_page', {
            'brands': brands,
            'default_brand': default_brand,
            'product': default_product,
            'product_variant': None,
            'combination_info': None,
            'page_title': 'Anti-Yellow Clear Cases',
        })

    @http.route('/gadgetflix/anti-yellow/get_models', type='jsonrpc', auth='public', csrf=False)
    def gf_get_models(self, product_id):
        """Return model attribute values for a given product_id.
        Each entry carries enough data to identify the correct variant.
        """
        product = request.env['product.template'].sudo().browse(int(product_id))
        if not product.exists():
            return []

        model_line = product.attribute_line_ids.filtered(
            lambda l: l.attribute_id.name.lower() == 'model'
        )[:1]

        result = []
        for ptav in model_line.product_template_value_ids._only_active():
            attr_val = ptav.product_attribute_value_id

            # Find the variant that carries this model value
            variant = product.product_variant_ids.filtered(
                lambda v: attr_val.id in v.product_template_attribute_value_ids.mapped(
                    'product_attribute_value_id'
                ).ids
            )[:1]

            extra_images = []
            if variant:
                # Always put the main variant image first
                extra_images.append(f'/web/image/product.product/{variant.id}/image_512')
                for img in product.product_template_image_ids:
                    if not img.product_variant_id or variant.id == img.product_variant_id.id:
                        extra_images.append(f'/web/image/product.image/{img.id}/image_512')

            result.append({
                'id': attr_val.id,
                'name': attr_val.name,
                'product_id': product.id,
                'variant_id': variant.id if variant else 0,
                'price': variant.lst_price if variant else product.list_price,
                'image_url': f'/web/image/product.product/{variant.id}/image_512' if variant else '',
                'extra_image_urls': extra_images,
                'is_available': variant.qty_available >= 0 if variant else True,
            })

        return result
