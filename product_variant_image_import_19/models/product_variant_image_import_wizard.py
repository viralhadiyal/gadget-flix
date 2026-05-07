# -*- coding: utf-8 -*-
import base64
import json
import os
import tempfile

from odoo import _, fields, models
from odoo.exceptions import UserError

try:
    import openpyxl
except Exception:  # pragma: no cover
    openpyxl = None


class ProductVariantImageImportWizard(models.TransientModel):
    _name = "product.variant.image.import.wizard"
    _description = "Import Products With Variant Images From Excel"

    file = fields.Binary(string="Excel File", required=True)
    filename = fields.Char(string="Filename")
    update_existing = fields.Boolean(string="Update Existing Products", default=True)
    clear_existing_extra_images = fields.Boolean(
        string="Clear Existing Extra Images Before Import",
        default=False,
        help="If enabled, removes existing product.image records for the product template before creating new extra images.",
    )

    # -------------------------------------------------------------------------
    # Generic helpers
    # -------------------------------------------------------------------------
    def _normalize(self, value):
        return str(value or "").strip()

    def _json_loads(self, text, row_index, column_name, product_name):
        text = self._normalize(text)
        if not text:
            return {}
        try:
            return json.loads(text)
        except Exception as error:
            raise UserError(_(
                "Invalid JSON in row %(row)s, column %(column)s for product %(product)s.\n\n%(error)s"
            ) % {
                "row": row_index,
                "column": column_name,
                "product": product_name or "-",
                "error": error,
            })

    def _image_to_base64(self, image_path):
        image_path = self._normalize(image_path)
        if not image_path:
            return False

        # This importer is for local server paths. The path must be visible to the Odoo server user.
        if not os.path.isfile(image_path):
            raise UserError(_("Image not found on the Odoo server: %s") % image_path)

        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read())

    def _as_bool(self, value, default=True):
        if value in (None, ""):
            return default
        return self._normalize(value).lower() in ("1", "true", "yes", "y")

    # -------------------------------------------------------------------------
    # Get/create helpers
    # -------------------------------------------------------------------------
    def _get_or_create_attribute(self, name):
        name = self._normalize(name)
        if not name:
            raise UserError(_("Attribute name is empty."))

        Attribute = self.env["product.attribute"]
        attribute = Attribute.search([("name", "=", name)], limit=1)
        if attribute:
            return attribute

        vals = {"name": name}
        if "create_variant" in Attribute._fields:
            vals["create_variant"] = "always"
        return Attribute.create(vals)

    def _get_or_create_attribute_value(self, attribute, value):
        value = self._normalize(value)
        if not value:
            raise UserError(_("Attribute value is empty for attribute %s.") % attribute.name)

        AttributeValue = self.env["product.attribute.value"]
        attr_value = AttributeValue.search([
            ("attribute_id", "=", attribute.id),
            ("name", "=", value),
        ], limit=1)
        if attr_value:
            return attr_value

        return AttributeValue.create({
            "attribute_id": attribute.id,
            "name": value,
        })

    def _get_or_create_internal_category(self, category_name):
        category_name = self._normalize(category_name) or "All"
        Category = self.env["product.category"]
        category = Category.search([("name", "=", category_name)], limit=1)
        if category:
            return category
        return Category.create({"name": category_name})

    def _get_or_create_public_category(self, category_name):
        category_name = self._normalize(category_name) or "All"
        PublicCategory = self.env["product.public.category"]
        public_category = PublicCategory.search([("name", "=", category_name)], limit=1)
        if public_category:
            return public_category
        return PublicCategory.create({"name": category_name})

    def _get_or_create_product_template(self, row_data, attributes_data, images_data):
        ProductTemplate = self.env["product.template"]

        product_name = self._normalize(row_data.get("Product Name"))
        default_code = self._normalize(row_data.get("Internal Reference"))
        category_name = self._normalize(row_data.get("Category")) or "All"
        ecommerce_category_name = self._normalize(row_data.get("Ecommerce Category")) or category_name
        sales_price = row_data.get("Sales Price")
        publish = self._as_bool(row_data.get("Publish"), default=True)

        if not product_name:
            raise UserError(_("Product Name is required."))

        domain = []
        if default_code:
            domain = [("default_code", "=", default_code)]
        else:
            domain = [("name", "=", product_name)]

        product_tmpl = ProductTemplate.search(domain, limit=1)
        if product_tmpl and not self.update_existing:
            raise UserError(_("Product already exists and Update Existing Products is disabled: %s") % product_name)

        internal_category = self._get_or_create_internal_category(category_name)
        ecommerce_category = self._get_or_create_public_category(ecommerce_category_name)

        vals = {
            "name": product_name,
            "categ_id": internal_category.id,
            "sale_ok": True,
            "purchase_ok": True,
        }

        if default_code and "default_code" in ProductTemplate._fields:
            vals["default_code"] = default_code
        if sales_price not in (None, "") and "list_price" in ProductTemplate._fields:
            vals["list_price"] = float(sales_price)
        if "is_published" in ProductTemplate._fields:
            vals["is_published"] = publish
        if "public_categ_ids" in ProductTemplate._fields:
            vals["public_categ_ids"] = [(6, 0, [ecommerce_category.id])]

        # Odoo versions may expose either type or detailed_type. Set safely only when available.
        if "type" in ProductTemplate._fields:
            vals["type"] = "consu"
        elif "detailed_type" in ProductTemplate._fields:
            vals["detailed_type"] = "consu"

        if product_tmpl:
            product_tmpl.write(vals)
        else:
            product_tmpl = ProductTemplate.create(vals)

        return product_tmpl

    # -------------------------------------------------------------------------
    # Image helpers
    # -------------------------------------------------------------------------
    def _create_extra_images(self, product_tmpl, image_paths, variant=False):
        if not image_paths:
            return

        if isinstance(image_paths, str):
            image_paths = [path.strip() for path in image_paths.split(",") if path.strip()]

        ProductImage = self.env["product.image"]
        for image_path in image_paths:
            image_path = self._normalize(image_path)
            if not image_path:
                continue

            vals = {
                "name": os.path.basename(image_path),
                "product_tmpl_id": product_tmpl.id,
                "image_1920": self._image_to_base64(image_path),
            }
            if variant and "product_variant_id" in ProductImage._fields:
                vals["product_variant_id"] = variant.id

            ProductImage.create(vals)

    def _apply_template_images(self, product_tmpl, images_data):
        if self.clear_existing_extra_images:
            self.env["product.image"].search([("product_tmpl_id", "=", product_tmpl.id)]).unlink()

        main_image = images_data.get("main_image")
        if main_image and "image_1920" in product_tmpl._fields:
            product_tmpl.image_1920 = self._image_to_base64(main_image)

        self._create_extra_images(product_tmpl, images_data.get("main_extra_images", []))

    # -------------------------------------------------------------------------
    # Attribute/variant helpers
    # -------------------------------------------------------------------------
    def _prepare_attribute_lines_and_variant_images(self, attributes_data):
        """Return attribute lines and image mapping.

        Supported Attributes JSON:
        {
          "brand": "apple",
          "colour": {
            "red": {"main_image": "/path/red.jpg", "main_extra_images": ["/path/red_1.jpg"]},
            "black": {"main_image": "/path/black.jpg", "main_extra_images": []}
          },
          "case type": "silicon"
        }

        Also supports an explicit exact-combination key:
        {
          "brand": "apple",
          "colour": ["red", "black"],
          "size": ["S", "M"],
          "variant_images": [
            {"values": {"colour":"red", "size":"S"}, "main_image":"/path/red_s.jpg"}
          ]
        }
        """
        attribute_lines = []
        variant_image_map = []

        explicit_variant_images = attributes_data.get("variant_images") or []

        for attribute_name, value_data in attributes_data.items():
            if attribute_name == "variant_images":
                continue

            attribute = self._get_or_create_attribute(attribute_name)
            value_ids = []

            if isinstance(value_data, dict):
                for value_name, image_data in value_data.items():
                    attr_value = self._get_or_create_attribute_value(attribute, value_name)
                    value_ids.append(attr_value.id)
                    if isinstance(image_data, dict):
                        variant_image_map.append({
                            "values": {attribute_name: value_name},
                            "main_image": image_data.get("main_image"),
                            "extra_images": image_data.get("main_extra_images", []),
                        })
            elif isinstance(value_data, list):
                for value_name in value_data:
                    attr_value = self._get_or_create_attribute_value(attribute, value_name)
                    value_ids.append(attr_value.id)
            else:
                attr_value = self._get_or_create_attribute_value(attribute, value_data)
                value_ids.append(attr_value.id)

            attribute_lines.append({
                "attribute_id": attribute.id,
                "value_ids": value_ids,
            })

        for item in explicit_variant_images:
            if not isinstance(item, dict) or not item.get("values"):
                continue
            variant_image_map.append({
                "values": item.get("values"),
                "main_image": item.get("main_image"),
                "extra_images": item.get("main_extra_images", []),
            })

        return attribute_lines, variant_image_map

    def _apply_attribute_lines(self, product_tmpl, attribute_lines):
        AttributeLine = self.env["product.template.attribute.line"]

        for line_data in attribute_lines:
            existing_line = product_tmpl.attribute_line_ids.filtered(
                lambda line: line.attribute_id.id == line_data["attribute_id"]
            )
            if existing_line:
                existing_line.write({"value_ids": [(6, 0, line_data["value_ids"])]})
            else:
                AttributeLine.create({
                    "product_tmpl_id": product_tmpl.id,
                    "attribute_id": line_data["attribute_id"],
                    "value_ids": [(6, 0, line_data["value_ids"])],
                })

        product_tmpl._create_variant_ids()
        product_tmpl.invalidate_recordset()

    def _find_variant_by_values(self, product_tmpl, values_map):
        """Find variant containing all attribute=value pairs in values_map."""
        normalized_values = {
            self._normalize(attr).lower(): self._normalize(value).lower()
            for attr, value in (values_map or {}).items()
        }

        for variant in product_tmpl.product_variant_ids:
            matched = 0
            ptavs = variant.product_template_attribute_value_ids
            for attribute_name, value_name in normalized_values.items():
                found = ptavs.filtered(
                    lambda ptav: self._normalize(ptav.attribute_id.name).lower() == attribute_name
                    and self._normalize(ptav.product_attribute_value_id.name or ptav.name).lower() == value_name
                )
                if found:
                    matched += 1
            if matched == len(normalized_values):
                return variant
        return False

    def _apply_variant_images(self, product_tmpl, variant_image_map, product_name):
        for image_data in variant_image_map:
            variant = self._find_variant_by_values(product_tmpl, image_data.get("values"))
            if not variant:
                raise UserError(_(
                    "Variant not found for product %(product)s with attribute values %(values)s"
                ) % {
                    "product": product_name,
                    "values": image_data.get("values"),
                })

            main_image = image_data.get("main_image")
            if main_image and "image_1920" in variant._fields:
                variant.image_1920 = self._image_to_base64(main_image)

            self._create_extra_images(
                product_tmpl,
                image_data.get("extra_images", []),
                variant=variant,
            )

    # -------------------------------------------------------------------------
    # Import action
    # -------------------------------------------------------------------------
    def action_import_products(self):
        self.ensure_one()

        if openpyxl is None:
            raise UserError(_("Python package openpyxl is required. Install it on the Odoo server."))

        if not self.file:
            raise UserError(_("Please upload an Excel file."))

        file_data = base64.b64decode(self.file)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as temp:
            temp.write(file_data)
            temp_path = temp.name

        workbook = openpyxl.load_workbook(temp_path, data_only=True)
        sheet = workbook.active

        headers = [self._normalize(cell.value) for cell in sheet[1]]
        required_headers = ["Product Name", "Category", "Attributes", "Images"]
        missing_headers = [header for header in required_headers if header not in headers]
        if missing_headers:
            raise UserError(_("Missing Excel columns: %s") % ", ".join(missing_headers))

        imported_count = 0
        for row_index, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
            row_data = dict(zip(headers, row))
            product_name = self._normalize(row_data.get("Product Name"))
            if not product_name:
                continue

            attributes_data = self._json_loads(row_data.get("Attributes"), row_index, "Attributes", product_name)
            images_data = self._json_loads(row_data.get("Images"), row_index, "Images", product_name)

            product_tmpl = self._get_or_create_product_template(row_data, attributes_data, images_data)
            self._apply_template_images(product_tmpl, images_data)

            attribute_lines, variant_image_map = self._prepare_attribute_lines_and_variant_images(attributes_data)
            self._apply_attribute_lines(product_tmpl, attribute_lines)
            self._apply_variant_images(product_tmpl, variant_image_map, product_name)

            imported_count += 1

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Import Complete"),
                "message": _("Imported/updated %s product template(s).") % imported_count,
                "type": "success",
                "sticky": False,
            },
        }
