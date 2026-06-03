{
    "name": "Shiprocket Integration",
    "summary": "Shiprocket connector for rates, labels, pickup, and tracking",
    "description": "Connect delivery methods with Shiprocket for courier pricing, shipment booking, labels, manifests, and cancellation.",
    "category": "Shipping Connectors",
    "sequence": 318,
    "version": "19.0.0.1",
    "author": "GadgetFlix",
    "application": True,
    "depends": ["stock_delivery", "mail"],
    "data": [
        "security/ir.model.access.csv",
        "data/shipping_data.xml",
        "views/delivery_method_views.xml",
        "views/stock_transfer_views.xml",
    ],
    "license": "LGPL-3",
}
