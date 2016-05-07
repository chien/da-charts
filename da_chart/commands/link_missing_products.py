
import re

from flask.ext.script import Command as BaseCommand, Option
from flask import current_app as app, render_template
from semantics3 import Products as SemanticProducts
from semantics3.error import Semantics3Error

from retsku.api.models import db, Submission, Product, LogAction, Brand
from retsku.api.common import gtin_validator
from retsku.api.common import retsku_api
from retsku.api.common import email as email_service


class Command(BaseCommand):
    def run(self):
        app.logger.info('Run link missing ret_sku_id/retsku_product_id.')

        submissions = self._get_submissions()
        app.logger.debug('Found {} submission without product.'.format(
            submissions.count()))

        products_wrong_category = []

        for submission in submissions:
            task = submission.assignment.task
            if task.retailer_id is None:
                app.logger.debug('Task retailer id should be specified.')
                continue

            product = self._get_product(task.retailer_id,
                                        submission)

            if product is None:
                continue

            if product.retsku_category_id != task.retsku_category_id:
                product.task_retsku_category_id = task.retsku_category_id
                products_wrong_category.append(product)

            self._add_log(submission.id, 'update submission',
                          submission.ret_sku_id, product.ret_sku_id)
            submission.product = product
            submission.retsku_product_id = product.retsku_product_id
            app.logger.debug(
                    'Processing submission {}: Updating ret_sku_id: {}, retsku_product_id: {}'.format(
                    submission.id, product.ret_sku_id, product.retsku_product_id))
            db.session.commit()

        if products_wrong_category:
            html = render_template('email/missing_products.html',
                                   products=products_wrong_category)
            email_service.send_mail(app.config['DEFAULT_MAIL_TO'],
                                    'Products with categories mismatch',
                                    html)

    def _get_submissions(self):
        return Submission.query.filter(
            Submission.ret_sku_id == None,
            Submission.barcode != None).order_by(
            Submission.updated_at.desc())

    def _get_product(self, retailer_id, submission):
        products = Product.query.filter(Product.retsku_product_id != None).filter(Product.retailer_id == retailer_id, ((Product.barcode == submission.barcode) |
            (Product.retsku_product_id == submission.retsku_product_id))).all()

        if products:
            # if we have list use first or try to find with the same values
            return products[0]
        else:
            return None

    def _add_log(self, item_id, action, old_value, new_value):
        action = LogAction(item_id=item_id, action=action,
                           old_value=old_value, new_value=new_value)
        db.session.add(action)
        db.session.commit()
