from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    facebook_pixel_id = fields.Char(related='website_id.facebook_pixel_id', readonly=False)
    facebook_capi_token = fields.Char(related='website_id.facebook_capi_token', readonly=False)
    facebook_capi_test_code = fields.Char(related='website_id.facebook_capi_test_code', readonly=False)
    facebook_capi_api_version = fields.Char(related='website_id.facebook_capi_api_version', readonly=False)
