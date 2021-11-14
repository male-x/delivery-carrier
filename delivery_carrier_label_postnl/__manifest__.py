# Copyright 2021 Alexander Makarychev
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Carrier labels for PostNL",
    "version": "12.0.1.0.0",
    "development_status": "Alpha",
    "category": "Delivery",
    "website": "https://github.com/OCA/delivery-carrier",
    "author": "Alexander Makarychev,Odoo Community Association (OCA)",
    "maintainers": ["male-x"],
    'installable': True,
    'auto_install': False,
    "license": "AGPL-3",
    "application": False,
    "depends": [
        "base_address_extended",
        "base_delivery_carrier_label",
    ],
    "data": [
        "data/delivery_carrier_data.xml",
        "data/ir_config_parameter_data.xml",
        "views/carrier_account.xml",
    ],
    "demo": [],
}
