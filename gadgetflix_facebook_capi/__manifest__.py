{
    'name': 'Gadgetflix - Facebook Conversion API',
    'version': '1.0',
    'category': 'Website/Website',
    'summary': 'Facebook Conversion API (CAPI) and Advanced Pixel Tracking',
    'description': """
        Sends server-side Purchase events to Facebook Conversion API to bypass adblockers.
        Also tracks ViewContent, AddToCart, and InitiateCheckout with Event IDs for deduplication.
    """,
    'depends': ['website_sale', 'sale'],
    'data': [
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
