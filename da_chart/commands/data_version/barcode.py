
from flask_restful import fields

from retsku.commands.data_version.base import Command as BaseCommand
from retsku.api.models import BarcodePattern
from retsku.api import const


class Command(BaseCommand):

    need_validation = False
    json_fields = {
        'ret_sku_id': fields.Integer,
        'retsku_category_id': fields.Integer(
            attribute='task.retsku_category_id', default=None),
        'retailer_id': fields.Integer(attribute='task.retailer_id',
                                      default=None),
        'retsku_product_id': fields.Integer(
            attribute='product.retsku_product_id', default=None),
        'pattern': fields.String,
        'brand_name': fields.String(attribute='product.brand.brand_name'),
        'brand_id': fields.String(attribute='product.brand_id'),
        'model_name': fields.String(attribute='product.model_name')}

    data_version_type = const.DATA_TYPES['barcode']

    def get_data(self):
        return BarcodePattern.query.filter(
            BarcodePattern.task_id == self.task.id).all()
