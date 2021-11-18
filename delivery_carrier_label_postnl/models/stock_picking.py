# Copyright 2021 Alexander Makarychev
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import datetime
import requests

from odoo import _, models
from odoo.exceptions import UserError
from odoo.tools import datetime

from .delivery_carrier import DELIVERY_TYPE_POSTNL

POSTNL_REQUEST_TYPE_BARCODE = "barcode"
POSTNL_REQUEST_TYPE_LABEL = "label"


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def action_generate_carrier_label(self):
        # Labels for PostNL pickings are generated during send action
        filtered = self.filtered(lambda x: x.carrier_id.delivery_type != DELIVERY_TYPE_POSTNL)
        return super(StockPicking, filtered).action_generate_carrier_label()

    def _postnl_send(self):
        """
        Send shipment of the picking to PostNL,
        save retrieved label and barcode for tracking

        :return: A list of dictionaries suitable for delivery.carrier#send_shipping
        """
        return [picking._postnl_send_shipment() for picking in self]

    def _postnl_request_barcode(self, carrier_account, request_headers):
        """
        Send barcode API request
        :see: https://developer.postnl.nl/browse-apis/send-and-track/barcode-webservice/documentation-soap/
        :version: Interface version 1_1
        """
        self.ensure_one()

        request_body = {
            "CustomerCode": carrier_account.postnl_customer_code,
            "CustomerNumber": carrier_account.postnl_customer_number,
            "Type": carrier_account.postnl_barcode_type,
        }

        response = requests.post(
            url=self._postnl_request_url(POSTNL_REQUEST_TYPE_BARCODE),
            json=request_body,
            headers=request_headers,
        ).json()

        try:
            return response["Barcode"]
        except KeyError:
            self._postnl_raise_error(POSTNL_REQUEST_TYPE_BARCODE, response, KeyError)

    def _postnl_send_shipment(self):
        """
        Send shipment label API request
        :see: https://developer.postnl.nl/browse-apis/send-and-track/labelling-webservice/documentation/
        :version: Interface version 2_2
        """
        self.ensure_one()

        carrier_account = self._postnl_carrier_account()
        request_headers = {
            "apikey": carrier_account.postnl_api_key,
            "accept": "application/json",
            "content-type": "application/json",
        }

        barcode = self._postnl_request_barcode(carrier_account, request_headers)

        request_body = {
            "Customer": {
                "Address": {
                    "AddressType": "02",
                    "City": self.company_id.city,
                    "CompanyName": self.company_id.name,
                    "Countrycode": self.company_id.country_id.code,
                    "Street": self.company_id.street,
                    "Zipcode": self.company_id.zip,
                },
                "CollectionLocation": carrier_account.postnl_collection_location,
                "CustomerCode": carrier_account.postnl_customer_code,
                "CustomerNumber": str(carrier_account.postnl_customer_number),
            },
            "Message": {
                "MessageID": "1",
                "MessageTimeStamp": datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
                "Printertype": "GraphicFile|PDF",
            },
            "Shipments": {
                "Addresses": [
                    {
                        "AddressType": "01",
                        "City": self.partner_id.city,
                        "Countrycode": self.partner_id.country_id.code,
                        "HouseNr": self.partner_id.street_number,
                        "HouseNrExt": self.partner_id.street_number2,
                        "Name": self.partner_id.name,
                        "Street": self.partner_id.street_name,
                        "Zipcode": self.partner_id.zip,
                    }
                ],
                "Barcode": barcode,
                "DeliveryAddress": "01",
                "Dimension": {
                    "Weight": self.shipping_weight,
                    "Volume": self.volume,
                },
                "ProductCodeDelivery": "4945"  # Commercial Goods, Commercial Sample, Returned Goods
            }
        }

        response = requests.post(
            url=self._postnl_request_url(POSTNL_REQUEST_TYPE_LABEL),
            json=request_body,
            headers=request_headers,
        ).json()

        try:
            shipment_data = response["ResponseShipments"][0]
            return {
                "exact_price": 0,
                "tracking_number": shipment_data["Barcode"],
                "labels": [{
                    "name": label["Labeltype"],
                    "file": label["Content"],
                    "file_type": "pdf",
                } for label in shipment_data["Labels"]],
            }
        except KeyError:
            self._postnl_raise_error(POSTNL_REQUEST_TYPE_LABEL, response, KeyError)

    def _postnl_request_url(self, request_type):
        return self.env["ir.config_parameter"].sudo().get_param(
            "delivery_carrier_label_postnl.%(request_type)s_endpoint_%(environment)s"
            % {
                "environment": "production" if self.carrier_id.prod_environment else "sandbox",
                "request_type": request_type,
            }
        )

    def _postnl_carrier_account(self):
        """
        Find a PostNL carrier account for the current company
        or fallback to non-company PostNL account if it exists

        :raise: odoo.exceptions.UserError if no carrier account was found
        :return: carrier.account record
        """
        self.ensure_one()
        carrier_account = self.env["carrier.account"].search(
            [
                ("delivery_type", "=", DELIVERY_TYPE_POSTNL),
                "|", ("company_id", "=", False), ("company_id", "=", self.company_id.id),
            ],
            limit=1,
            order="company_id ASC",  # Current company PostNL account is prioritised
        )

        if not carrier_account:
            raise UserError(_("Please create PostNL carrier account for %(company_name)s company.")
                            % {"company_name": self.company_id.name})

        return carrier_account

    def _postnl_raise_error(self, request_type, response, reraise):
        """Try to extract error message from invalid response"""
        for item in response:
            if "ErrorMsg" in item:
                raise UserError(
                    _("PostNL %(request_type)s API exception: %(error_number)d %(error_msg)s")
                    % {
                        "request_type": request_type,
                        "error_number": item["ErrorNumber"],
                        "error_msg": item["ErrorMsg"],
                    }
                )

        raise reraise

    def _postnl_get_tracking_link(self):
        """
        Tracking URL of PostNL shipment
        :return: Tracking link string
        :todo: Determine which countries do not use postal codes
        """
        self.ensure_one()

        return ("https://tracking.postnl.nl/track-and-trace/"
                "%(tracking_reference)s-%(country_code)s-%(postal_code)s") % {
            "tracking_reference": self.carrier_tracking_ref,
            "country_code": self.partner_id.country_id.code,
            "postal_code": self.partner_id.zip,
        }
