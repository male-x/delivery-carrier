# Copyright 2021 Alexander Makarychev
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.base_delivery_carrier_label.tests import carrier_label_case

from odoo.addons.delivery_carrier_label_postnl.models.delivery_carrier import DELIVERY_TYPE_POSTNL


class DeliveryCarrierLabelPostnlCase(carrier_label_case.CarrierLabelCase):
    def _create_carrier_account(self):
        return self.env["carrier.account"].create({
            "name": "PostNL carrier account",
            "delivery_type": DELIVERY_TYPE_POSTNL,
        })

    def _create_order_picking(self):
        self._create_carrier_account()
        super()._create_order_picking()

    def _get_carrier(self):
        return self.env.ref("delivery_carrier_label_postnl.carrier_postnl")


class TestDeliveryCarrierLabelPostnl(
        DeliveryCarrierLabelPostnlCase,
        carrier_label_case.TestCarrierLabel):
    pass
