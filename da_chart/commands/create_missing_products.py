
import re

from flask.ext.script import Command as BaseCommand, Option
from flask import current_app as app, render_template
from semantics3 import Products as SemanticProducts
from semantics3.error import Semantics3Error
from sqlalchemy import func

from retsku.api.models import db, Submission, Product, LogAction, Brand
from retsku.api.common import gtin_validator
from retsku.api.common import retsku_api
from retsku.api.common import email as email_service


class Command(BaseCommand):

    # string with numbers, max length is 14 chars
    UPC_REGEXP = re.compile('^\d{1,14}$')

    option_list = (
        Option('--limit', dest='limit', type=int),)

    def run(self, limit=None):
        app.logger.info('Run create missing products.')

        self.product_finder = SemanticProducts(**app.config['SEMANTICS3'])

        submissions = self._get_submissions()
        app.logger.debug('Found {} submission without product.'.format(
            submissions.count()))

        products_wrong_category = []

        if limit:
            app.logger.debug('Applied limit: {}.'.format(limit))
            submissions = submissions.limit(limit)

        for submission in submissions:
            task = submission.assignment.task
            app.logger.debug('Processing submission {}.'.format(submission.id))
            app.logger.debug('Retailer {}, category: {}.'.format(
                task.retailer_id, task.retsku_category_id))

            if task.retailer_id is None:
                app.logger.debug('Task retailer id should be specified.')
                continue

            gtin = None
            if self.UPC_REGEXP.match(submission.scanned_upc):
                gtin = gtin_validator.validate_GTIN(submission.scanned_upc)

            if gtin is None:
                app.logger.debug(
                    'Submission upc {} is not valid GTIN'.format(
                        submission.scanned_upc))
                continue

            product = self._get_product(task.retailer_id, gtin,
                                        task.retsku_category_id,
                                        submission)

            if product is None:
                app.logger.debug('Couldn\'t create product.')
                continue

            if product.retsku_category_id != task.retsku_category_id:
                product.task_retsku_category_id = task.retsku_category_id
                products_wrong_category.append(product)

            if not product.retsku_product_id:
                self._update_retsku_product_id(product)

            self._add_log(submission.id, 'update submission',
                          submission.ret_sku_id, product.ret_sku_id)
            submission.product = product
            submission.retsku_product_id = product.retsku_product_id
            app.logger.debug(
                'Updating ret_sku_id: {}, retsku_product_id: {}'.format(
                    product.ret_sku_id, product.retsku_product_id))
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
            Submission.scanned_upc != None,
            Submission.barcode != None).order_by(
            Submission.updated_at.desc())

    def _get_product(self, retailer_id, gtin, retsku_category_id,
                     submission):
        products = Product.query.filter(
            Product.retailer_id == retailer_id,
            Product.gtin == gtin).all()
        if not products:
            products = Product.query.filter(
                Product.retailer_id == retailer_id,
                Product.barcode == submission.barcode).all()

        if products:
            # if we have list use first or try to find with the same values
            for p in products:
                if p.gtin == gtin and p.barcode == submission.barcode:
                    product = p
                    break
            else:
                product = products[0]

            if product.barcode != submission.barcode:
                app.logger.debug(
                    'Updating barcode for {}. Old: {}, new: {}.'.format(
                        product.ret_sku_id, product.barcode,
                        submission.barcode))
                self._add_log(product.ret_sku_id, 'update barcode',
                              product.barcode, submission.barcode)
                product.barcode = submission.barcode
                db.session.commit()

            if product.gtin != gtin:
                app.logger.debug(
                    'Updating GTIN for {}. Old: {}, new: {}.'.format(
                        product.ret_sku_id, product.gtin, gtin))
                self._add_log(product.ret_sku_id, 'update gtin', product.gtin,
                              gtin)
                product.gtin = gtin
                db.session.commit()
        else:
            product = self._create_product(retailer_id, gtin,
                                           retsku_category_id, submission)

        return product

    def _create_product(self, retailer_id, gtin, retsku_category_id,
                        submission):

        if submission.brand is None or submission.model is None:
            semantics_info = self._get_semantics_info(submission.scanned_upc)
        else:
            semantics_info = {}

        # get or create brand
        brand_name = submission.brand or semantics_info.get('brand')
        if not brand_name:
            return None

        brand_name = brand_name.strip()
        brand = Brand.query.filter(
            func.lower(Brand.brand_name) == func.lower(brand_name)).first()
        if not brand:
            brand = Brand(brand_name=brand_name)
            db.session.add(brand)
            db.session.commit()
            self._add_log(brand.brand_id, 'create new brand', None, None)

        model = submission.model or semantics_info.get('model') or gtin
        product = Product(retailer_id=retailer_id,
                          retsku_category_id=retsku_category_id,
                          gtin=gtin,
                          barcode=submission.barcode,
                          external_product_code=gtin,
                          model_name=model,
                          brand=brand,
                          semantic_id=semantics_info.get('semantic_id'))
        db.session.add(product)
        db.session.commit()
        self._add_log(product.ret_sku_id, 'create new product', None, None)
        return product

    def _update_retsku_product_id(self, product):
        result = retsku_api.get_retsku_product_id(
            brand_name=product.brand.brand_name,
            semantic_id=product.semantic_id,
            model_name=product.model_name,
            product_code=product.external_product_code,
            gtin=product.gtin)

        if result:
            self._add_log(product.ret_sku_id, 'update retsku product id',
                          product.retsku_product_id,
                          result['retsku_product_id'])

            product.retsku_product_id = result['retsku_product_id']
            product.matcher_type = result['matcher_type']
            # yr: do we need update retsku_category_id?
            db.session.commit()

    def _add_log(self, item_id, action, old_value, new_value):
        action = LogAction(item_id=item_id, action=action,
                           old_value=old_value, new_value=new_value)
        db.session.add(action)
        db.session.commit()

    def _get_semantics_info(self, upc):
        self.product_finder.clear_query()
        self.product_finder.products_field('upc', upc)

        try:
            json_data = self.product_finder.get()
            if json_data.get('results', None):
                item = json_data['results'][0]
                return {
                    'semantic_id': item.get('sem3_id'),
                    'brand': item.get('brand', item.get('manufacturer')),
                    'model': item.get('model', item.get('mpn'))}
            return {}
        except (ValueError, Semantics3Error):
            return {}
