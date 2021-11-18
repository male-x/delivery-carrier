# Copyright 2021 Alexander Makarychev
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

from .delivery_carrier import DELIVERY_TYPE_POSTNL


class CarrierAccount(models.Model):
    _inherit = "carrier.account"

    is_postnl = fields.Boolean(compute="_compute_is_postnl", readonly=True)
    postnl_api_key = fields.Char()
    postnl_barcode_type = fields.Char(default="3S")
    postnl_collection_location = fields.Char(help="Code of delivery location at PostNL Pakketten")
    postnl_customer_code = fields.Char(
        default="DEVC",
        help="Customer code as known at PostNL Pakketten",
    )
    postnl_customer_number = fields.Integer(
        default="11223344",
        help="Customer number as known at PostNL Pakketten",
    )

    @api.depends("delivery_type")
    def _compute_is_postnl(self):
        for carrier_account in self:
            carrier_account.is_postnl = carrier_account.delivery_type == DELIVERY_TYPE_POSTNL
