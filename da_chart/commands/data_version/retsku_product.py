
from flask.ext.script import Command as BaseCommand, Option
from flask import current_app as app

from retsku.api.common import retsku_api


class Command(BaseCommand):

    option_list = (
        Option('--retsku_category_id', '-c', dest='retsku_category_id',
               required=True, type=int),
    )

    def run(self, retsku_category_id):
        # retsku api will generate file, save it so s3 and call instore api
        # to create data version and assing it to tasks
        app.logger.info('Run retsku_products for category {}.'.format(
            retsku_category_id))

        retsku_api.create_retsku_product_file(retsku_category_id)

        app.logger.info('Done.')
