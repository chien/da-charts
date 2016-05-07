
import re

from flask.ext.script import Command as BaseCommand, Option
from flask import current_app as app, render_template
from semantics3 import Products as SemanticProducts
from semantics3.error import Semantics3Error

from retsku.api.models import db, Submission, LogAction
from retsku.api.common import gtin_validator
from retsku.api.common import retsku_api
from retsku.api.common import email as email_service


class Command(BaseCommand):

    # string with numbers, max length is 14 chars
    UPC_REGEXP = re.compile('^\d{1,14}$')

    option_list = (
        Option('--limit', dest='limit', type=int),)

    def run(self, limit=None):
        app.logger.info('Run update submissions product.')

        self.product_finder = SemanticProducts(**app.config['SEMANTICS3'])

        submissions = self._get_submissions()
        app.logger.debug('Found {} submission without product.'.format(
            submissions.count()))

        not_linked_subs = []

        if limit:
            app.logger.debug('Applied limit: {}.'.format(limit))
            submissions = submissions.limit(limit)

        for submission in submissions:
            app.logger.debug('Processing submission {}.'.format(submission.id))

            gtin = None
            if self.UPC_REGEXP.match(submission.scanned_upc):
                gtin = gtin_validator.validate_GTIN(submission.scanned_upc)

            if gtin is None:
                app.logger.debug(
                    'Submission upc {} is not valid GTIN'.format(
                        submission.scanned_upc))
                not_linked_subs.append(submission)
                continue

            product_info = self._get_product_info(gtin)
            if not product_info:
                not_linked_subs.append(submission)
                continue

            retsku_product_id = self._get_retsku_product_id(
                gtin, product_info['brand'], product_info['model'])

            if not retsku_product_id:
                not_linked_subs.append(submission)
                continue

            submission.retsku_product_id = retsku_product_id
            self._add_log(submission.id, 'update submission retsku product id',
                          None, retsku_product_id)

            app.logger.debug(('Updating retsku_product_id: {}'
                              '').format(submission.retsku_product_id))
            db.session.commit()

        if not_linked_subs:
            html = render_template('email/submissions_without_products.html',
                                   submissions=not_linked_subs)
            email_service.send_mail(app.config['DEFAULT_MAIL_TO'],
                                    'Submissions without retsku_product_id',
                                    html)

    def _get_submissions(self):
        return Submission.query.filter(
            Submission.ret_sku_id == None,
            Submission.retsku_product_id == None,
            Submission.scanned_upc != None,
            Submission.scanned_upc != '').order_by(
            Submission.updated_at.desc())

    def _get_retsku_product_id(self, gtin, brand, model):
        result = retsku_api.get_retsku_product_id(
            brand_name=brand, model_name=model, gtin=gtin)

        if result:
            return result['retsku_product_id']
        return None

    def _add_log(self, item_id, action, old_value, new_value):
        action = LogAction(item_id=item_id, action=action,
                           old_value=old_value, new_value=new_value)
        db.session.add(action)
        db.session.commit()

    def _get_product_info(self, upc):
        product_info = self._get_product_match_info(upc)
        return product_info or self._get_semantics_info(upc)

    def _get_product_match_info(self, upc):
        info = retsku_api.get_products_info(upc)
        if info:
            return {'brand': info['brand'],
                    'model': info['model']}
        return None

    def _get_semantics_info(self, upc):
        self.product_finder.clear_query()
        self.product_finder.products_field('upc', upc)

        try:
            json_data = self.product_finder.get()
            if json_data.get('results', None):
                item = json_data['results'][0]
                return {
                    'brand': item.get('brand', item.get('manufacturer')),
                    'model': item.get('model', item.get('mpn'))}
            return None
        except (ValueError, Semantics3Error):
            return None
