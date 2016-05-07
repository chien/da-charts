
from flask_restful import fields

from retsku.commands.data_version.base import Command as BaseCommand
from retsku.api.models import Product, Submission
from retsku.api import const


class Command(BaseCommand):

    json_fields = {
        'ret_sku_id': fields.Integer,
        'retsku_product_id': fields.Integer,
        'retsku_category_id': fields.Integer,
        'retailer_id': fields.Integer,
        'barcode': fields.String,
        'gtin': fields.String,
        'external_product_code': fields.String,
        'found_in_store': fields.Boolean}

    data_version_type = const.DATA_TYPES['retailer_product']

    def get_data(self):
        products = Product.query.filter(
            Product.retailer_id == self.task.retailer_id,
            Product.retsku_category_id == self.task.retsku_category_id)

        ret_sku_ids = [p.ret_sku_id for p in products]
        submissions = Submission.query.with_entities(
            Submission.ret_sku_id).filter(
            Submission.ret_sku_id.in_(ret_sku_ids))
        found_ids = [s[0] for s in submissions]

        # we need to add found_in_store field
        retailer_products = []
        for p in products:
            # TODO yr: need to create some proxy to pass instance and new
            # attributes
            retailer_products.append(
                {'ret_sku_id': p.ret_sku_id,
                 'retsku_product_id': p.retsku_product_id,
                 'retailer_id': p.retailer_id,
                 'retsku_category_id': p.retsku_category_id,
                 'barcode': p.barcode,
                 'gtin': p.gtin,
                 'external_product_code': p.external_product_code,
                 'found_in_store': p.ret_sku_id in found_ids})
        return retailer_products

    def get_task(self, task_id):
        task = super().get_task(task_id)
        if task.retailer_id is None or task.retsku_category_id is None:
            raise Exception(('Task retailer_id and retsku_category_id'
                             'shouldn\'t be None'))
        return task
