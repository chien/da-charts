
from flask_restful import fields

from retsku.api.models import db
from retsku.api import const
from retsku.commands.data_version.base import Command as BaseCommand
from retsku.commands.data_version.price_pattern_manager import (
    PricePatternManager)


class Command(BaseCommand):

    json_fields = {
        'ret_sku_id': fields.Integer,
        'retsku_product_id': fields.Integer(default=None),
        'task_id': fields.Integer(attribute='task_id'),
        'pattern_id': fields.Integer(attribute='price_obj.price_pattern_id'),
        'retail_price': fields.Float,
        'floor_price': fields.Float,
        'no_of_facing': fields.Integer,
        'demo_location': fields.String,
        'demo_promotion': fields.String,
        'demo_display': fields.String,
        'no_of_shelves': fields.Integer,
        'in_store': fields.Boolean,
        'promotion_type_id': fields.Integer,
        'promotion': fields.String}

    data_version_type = const.DATA_TYPES['price']

    def get_data(self):
        manager = PricePatternManager(self.task)
        return manager.generate()

    def save(self, pattern_wrappers):
        price_wrappers = []
        for pattern_wrapper in pattern_wrappers:
            pattern = pattern_wrapper.get_obj()
            for price in pattern.prices:
                price.data_version = self.task_data_version.data_version
            db.session.add(pattern)

            price_wrappers.extend(pattern_wrapper.prices)

        db.session.commit()

        super().save(price_wrappers)
