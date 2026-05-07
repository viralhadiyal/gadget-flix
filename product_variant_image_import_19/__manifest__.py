{
    "name": "Product Variant Image Excel Import",
    "summary": "Import product templates, variants, website categories, and variant images from Excel JSON paths.",
    "version": "19.0.1.0.0",
    "category": "Sales/Sales",
    "author": "Custom",
    "license": "LGPL-3",
    "depends": ["product", "sale_management", "website_sale"],
    "data": [
        "security/ir.model.access.csv",
        "views/product_variant_image_import_wizard_views.xml",
    ],
    "installable": True,
    "application": False,
}
