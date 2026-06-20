{
    'name': 'Website Product Enhancement',
    'version': '19.0.1.1.0',
    'summary': 'Bulk Image Wizard + Attribute Search + Auto Ref + Weight Required',
    'description': """
        Features:
        1. Bulk Image Upload Wizard on Product Template form:
           - Upload multiple images for the template (first → main, rest → extra media)
           - Upload multiple images per variant with drag & drop reorder
           - Set weight in bulk (all variants) or per variant
        2. Website Shop search extended to match product attribute values
           (e.g. searching "Red" returns all products with a "Red" variant attribute)
        3. Auto Internal Reference: PROD-XXXXX is assigned on product creation
           if no internal reference is provided
        4. Weight Required: products cannot be saved with weight = 0
    """,
    'category': 'Website/eCommerce',
    "author": "Gadgetflix",
    'website': '',
    'license': 'LGPL-3',
    'depends': [
        'product',
        'website_sale',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'wizard/product_image_bulk_wizard_view.xml',
        'views/product_template_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
