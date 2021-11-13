# Copyright 2021 Alexander Makarychev
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(selection_add=[("postnl", "PostNL")],)

    def postnl_send_shipping(self, pickings):
        raise NotImplementedError()

    def postnl_get_tracking_link(self, picking):
        raise NotImplementedError()
