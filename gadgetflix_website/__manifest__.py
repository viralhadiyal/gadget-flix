# -*- coding: utf-8 -*-
{
    "name": "Gadgetflix Website",
    "summary": "Custom ecommerce website for Gadgetflix",
    "description": """
        Custom website pages, ecommerce styling, and website_sale extensions for Gadgetflix.
    """,
    "author": "Gadgetflix",
    "license": "LGPL-3",
    "version": "19.0.0.1",
    "category": "Website/Website",
    "depends": [
        "website_sale",
        "website_sale_wishlist",
        "website_mass_mailing",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/newsletter_data.xml",
        "views/backend_views.xml",
        "views/shop_by_device_menu_views.xml",
        "views/shop_templates.xml",
        "views/address_templates.xml",
        "views/portal_templates.xml",
        "views/mix_match_offer_views.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "gadgetflix_website/static/src/scss/gadgetflix_website.scss",
            "gadgetflix_website/static/src/js/gadgetflix_website.js",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}
