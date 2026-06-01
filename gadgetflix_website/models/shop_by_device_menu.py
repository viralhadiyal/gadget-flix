# -*- coding: utf-8 -*-

from odoo import fields, models


class GadgetflixShopByDeviceMenu(models.Model):
    _name = "gadgetflix.shop.by.device.menu"
    _description = "Shop by Device Menu"
    _order = "sequence, id"

    name = fields.Char(string="Title", required=True)
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    website_id = fields.Many2one("website", string="Website")
    link_ids = fields.One2many(
        "gadgetflix.shop.by.device.menu.link",
        "menu_id",
        string="Links",
    )


class GadgetflixShopByDeviceMenuLink(models.Model):
    _name = "gadgetflix.shop.by.device.menu.link"
    _description = "Shop by Device Menu Link"
    _order = "sequence, id"

    name = fields.Char(string="Label", required=True)
    url = fields.Char(string="Link", required=True)
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    menu_id = fields.Many2one(
        "gadgetflix.shop.by.device.menu",
        string="Menu Title",
        required=True,
        ondelete="cascade",
    )
