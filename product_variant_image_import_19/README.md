# Product Variant Image Excel Import for Odoo 19

This module imports product templates, variants, eCommerce categories, template images, and variant-specific images from a single Excel sheet.

## Install

1. Copy `product_variant_image_import_19` into your Odoo custom addons path.
2. Install server Python dependency:

```bash
pip3 install openpyxl
```

3. Restart Odoo and update Apps List.
4. Install **Product Variant Image Excel Import**.
5. Open menu: **Variant Image Import > Import Products**.

## Excel columns

Required:

- Product Name
- Category
- Attributes
- Images

Optional:

- Internal Reference
- Sales Price
- Ecommerce Category
- Publish
- Notes

## Important

Image paths like `/home/erp/images/test1_red.jpg` must exist on the Odoo server and be readable by the Odoo service user.

## Attributes JSON example

```json
{
  "brand": "apple",
  "colour": {
    "red": {
      "main_image": "/home/erp/images/test1_red.jpg",
      "main_extra_images": [
        "/home/erp/images/test1_red_1.jpg",
        "/home/erp/images/test1_red_2.jpg"
      ]
    },
    "black": {
      "main_image": "/home/erp/images/test1_black.jpg",
      "main_extra_images": [
        "/home/erp/images/test1_black_1.jpg",
        "/home/erp/images/test1_black_2.jpg"
      ]
    }
  },
  "case type": "silicon"
}
```

## Template Images JSON example

```json
{
  "main_image": "/home/erp/images/test1_main.jpg",
  "main_extra_images": [
    "/home/erp/images/test1_extra_1.jpg",
    "/home/erp/images/test1_extra_2.jpg"
  ]
}
```

## Exact variant-combination images

For products with multiple variant attributes, you can also use `variant_images` inside the Attributes JSON:

```json
{
  "brand": "apple",
  "colour": ["red", "black"],
  "size": ["S", "M"],
  "case type": "silicon",
  "variant_images": [
    {
      "values": {"colour": "red", "size": "S"},
      "main_image": "/home/erp/images/red_s.jpg",
      "main_extra_images": ["/home/erp/images/red_s_1.jpg"]
    }
  ]
}
```
