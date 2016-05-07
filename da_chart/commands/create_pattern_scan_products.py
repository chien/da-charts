
from flask.ext.script import Command as BaseCommand, Option
from flask import current_app as app
from sqlalchemy import func

from retsku.api.models import (db, PatternScanSubmission, Product, LogAction,
                               Brand, Assignment, Task, BarcodePattern)

DUMMY = 'dummy'


class Command(BaseCommand):

    option_list = (
        Option('--limit', dest='limit', type=int),)

    def run(self, limit=None):
        app.logger.info('Run create missing products for pattern scan '
                        'submissions.')

        submissions = self._get_submissions()
        app.logger.debug('Found {} submissions without product.'.format(
            submissions.count()))

        if limit:
            app.logger.debug('Applied limit: {}.'.format(limit))
            submissions = submissions.limit(limit)

        for submission in submissions:
            app.logger.debug('Processing submission {}.'.format(submission.id))

            brand_name = submission.brand.strip()
            brand = Brand.query.filter(
                func.lower(Brand.brand_name) == func.lower(brand_name))
            brand = brand.first()
            if not brand:
                brand = Brand(brand_name=brand_name)
                db.session.add(brand)
                db.session.commit()
                self._add_log(brand.brand_id, 'create new brand', None, None)

            product = self._get_or_create_product(submission, brand.brand_id)
            self._add_log(submission.id, 'update pattern scan submission',
                          submission.ret_sku_id, product.ret_sku_id)
            submission.product = product
            db.session.commit()

    def _get_submissions(self):
        return PatternScanSubmission.query.join(Assignment, Task).filter(
            PatternScanSubmission.ret_sku_id == None,
            PatternScanSubmission.brand != None,
            PatternScanSubmission.model != None,
            PatternScanSubmission.brand != '',
            PatternScanSubmission.model != '',
            Task.retailer_id != None,
            Task.retsku_category_id != None,
            Task.deleted == False,
            Assignment.deleted == False)

    def _get_or_create_product(self, sub, brand_id):
        sku = '{}-{}'.format(sub.brand.lower(), sub.model)
        product = Product.query.filter(
            Product.retailer_id == sub.assignment.task.retailer_id,
            Product.retsku_category_id == sub.assignment.task.retsku_category_id,
            Product.model_name == sub.model,
            Product.brand_id == brand_id,
            Product.external_product_code == sku).first()

        if product:
            return product

        product = Product(
            retailer_id=sub.assignment.task.retailer_id,
            retsku_category_id=sub.assignment.task.retsku_category_id,
            barcode=(sub.scanned_barcode or DUMMY),
            external_product_code=sku,
            model_name=sub.model,
            brand_id=brand_id)

        pattern = BarcodePattern(task=sub.assignment.task,
                                 product=product, pattern=DUMMY)
        db.session.add(pattern)
        db.session.add(product)
        db.session.commit()
        self._add_log(product.ret_sku_id, 'create new product', None, None)
        self._add_log(pattern.id, 'create new barcode pattern', None, None)
        return product

    def _add_log(self, item_id, action, old_value, new_value):
        action = LogAction(item_id=item_id, action=action,
                           old_value=old_value, new_value=new_value)
        db.session.add(action)
        db.session.commit()
