# Copyright 2021 Alexander Makarychev
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from unittest.mock import patch
from contextlib import contextmanager

from odoo.addons.base_delivery_carrier_label.tests import carrier_label_case
from odoo.addons.delivery_carrier_label_postnl.models.delivery_carrier import DELIVERY_TYPE_POSTNL
from odoo.exceptions import UserError


class DeliveryCarrierLabelPostnlCase(carrier_label_case.CarrierLabelCase):
    def _create_carrier_account(self):
        return self.env["carrier.account"].create({
            "name": "PostNL carrier account",
            "delivery_type": DELIVERY_TYPE_POSTNL,
            "account": "username",
            "password": "password",
            "postnl_api_key": "test",
        })

    def _create_order_picking(self, side_effect=None):
        self._create_carrier_account()
        with self._setup_mock_requests(side_effect):
            super()._create_order_picking()

    def _get_carrier(self):
        return self.env.ref("delivery_carrier_label_postnl.carrier_postnl")

    @contextmanager
    def _setup_mock_requests(self, side_effect=None):
        if side_effect is None:
            side_effect = [
                {"Barcode": "test_barcode"},
                {
                    "ResponseShipments": [
                        {
                            "ProductCodeDelivery": 0,
                            "Labels": [
                                {
                                    "Content": ("JVBERi0xLjQKJdPr6eEKMSAwIG9iago8PC9UaXRsZSAoVW50aX"
                                                "RsZWQgZG9jdW1lbnQpCi9Qcm9kdWNlciAoU2tpYS9QREYgbTk4"
                                                "IEdvb2dsZSBEb2NzIFJlbmRlcmVyKT4+CmVuZG9iagozIDAgb2"
                                                "JqCjw8L2NhIDEKL0JNIC9Ob3JtYWw+PgplbmRvYmoKNCAwIG9i"
                                                "ago8PC9MZW5ndGggODQ+PiBzdHJlYW0KMSAwIDAgLTEgMCA3OT"
                                                "IgY20KcQouNzUgMCAwIC43NSAwIDAgY20KMSAxIDEgUkcgMSAx"
                                                "IDEgcmcKL0czIGdzCjAgMCA4MTYgMTA1NiByZQpmClEKCmVuZH"
                                                "N0cmVhbQplbmRvYmoKMiAwIG9iago8PC9UeXBlIC9QYWdlCi9S"
                                                "ZXNvdXJjZXMgPDwvUHJvY1NldCBbL1BERiAvVGV4dCAvSW1hZ2"
                                                "VCIC9JbWFnZUMgL0ltYWdlSV0KL0V4dEdTdGF0ZSA8PC9HMyAz"
                                                "IDAgUj4+Pj4KL01lZGlhQm94IFswIDAgNjEyIDc5Ml0KL0Nvbn"
                                                "RlbnRzIDQgMCBSCi9TdHJ1Y3RQYXJlbnRzIDAKL1BhcmVudCA1"
                                                "IDAgUj4+CmVuZG9iago1IDAgb2JqCjw8L1R5cGUgL1BhZ2VzCi"
                                                "9Db3VudCAxCi9LaWRzIFsyIDAgUl0+PgplbmRvYmoKNiAwIG9i"
                                                "ago8PC9UeXBlIC9DYXRhbG9nCi9QYWdlcyA1IDAgUj4+CmVuZG"
                                                "9iagp4cmVmCjAgNwowMDAwMDAwMDAwIDY1NTM1IGYgCjAwMDAw"
                                                "MDAwMTUgMDAwMDAgbiAKMDAwMDAwMDI3NiAwMDAwMCBuIAowMD"
                                                "AwMDAwMTA3IDAwMDAwIG4gCjAwMDAwMDAxNDQgMDAwMDAgbiAK"
                                                "MDAwMDAwMDQ2NCAwMDAwMCBuIAowMDAwMDAwNTE5IDAwMDAwIG"
                                                "4gCnRyYWlsZXIKPDwvU2l6ZSA3Ci9Sb290IDYgMCBSCi9JbmZv"
                                                "IDEgMCBSPj4Kc3RhcnR4cmVmCjU2NgolJUVPRg=="),
                                    "Labeltype": "test_label_type",
                                }
                            ],
                            "Barcode": "test_barcode",
                            "Warnings": []
                        }
                    ]
                }
            ]
        with patch(
            "odoo.addons.delivery_carrier_label_postnl.models.stock_picking.requests"
        ) as mock_requests:
            mock_requests.post.return_value.json.side_effect = side_effect
            yield mock_requests


class TestDeliveryCarrierLabelPostnl(
        DeliveryCarrierLabelPostnlCase,
        carrier_label_case.TestCarrierLabel):

    def test_api_exception(self):
        with self.assertRaises(UserError):
            super()._create_order_picking([
                [{"ErrorMsg": "API exception message", "ErrorNumber": 555}]
            ])

    def test_tracking_url(self):
        super()._create_order_picking()

        delivery_carrier = self.env.ref('delivery_carrier_label_postnl.carrier_postnl')
        self.picking.partner_id.country_id = self.env.ref('base.nl')
        self.picking.partner_id.zip = "1111AA"

        expected = (
            "%(tracking_url)s%(tracking_reference)s-%(country_code)s-%(postal_code)s"
        ) % {
            "tracking_url": self.env["ir.config_parameter"].sudo().get_param(
                "delivery_carrier_label_postnl.tracking_url"
            ),
            "tracking_reference": self.picking.carrier_tracking_ref,
            "country_code": self.picking.partner_id.country_id.code,
            "postal_code": self.picking.partner_id.zip,
        }

        self.assertEqual(delivery_carrier.get_tracking_link(self.picking), expected)
