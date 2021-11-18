# Copyright 2021 Alexander Makarychev
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

DELIVERY_TYPE_POSTNL = "postnl"


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(selection_add=[(DELIVERY_TYPE_POSTNL, "PostNL")],)

    def postnl_send_shipping(self, pickings):
        return pickings._postnl_send()

    def postnl_get_tracking_link(self, picking):
        return picking._postnl_get_tracking_link()
