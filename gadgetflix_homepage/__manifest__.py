{
    'name': 'GadgetFlix Responsive Homepage',
    'version': '16.0.1.0.0',
    'summary': 'Modern responsive GadgetFlix ecommerce homepage for desktop and mobile',
    'category': 'Website/Website',
    'author': 'GadgetFlix',
    'depends': ['website', 'website_sale'],
    'data': [
        'views/homepage.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'gadgetflix_homepage/static/src/scss/gadgetflix_homepage.scss',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
