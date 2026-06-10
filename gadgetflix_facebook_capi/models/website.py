from odoo import fields, models

class Website(models.Model):
    _inherit = 'website'

    facebook_pixel_id = fields.Char(string="Facebook Pixel ID")
    facebook_capi_token = fields.Char(string="Facebook Conversion API Token")
    facebook_capi_test_code = fields.Char(string="Facebook Test Event Code", help="E.g. TEST12345 (used for testing in Events Manager)")
    facebook_capi_api_version = fields.Char(string="Facebook API Version", default="v19.0", help="E.g. v19.0 or v20.0")
