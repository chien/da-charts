
import json

import rollbar
from flask.ext.script import Command as BaseCommand, Option
from flask import current_app as app

from retsku.api.models import Task, DataVersion, TaskDataVersion, db
from retsku.api import const
from retsku.api.common import s3
from retsku.api.managers.task import TasksManager


class BaseValidator(object):
    """Base class for task data versions validation.

    Performs look up for entry all ret_sku_ids and retsku_product_ids in
    master type data versions searching from newest to older.
    """

    MASTER_STATUSES = [const.DATA_VERSION_STATUS['invalid'],
                       const.DATA_VERSION_STATUS['ready']]

    def __init__(self, task_dv):
        self.task_dv = task_dv
        self.current_products = None

    def validate(self, master_type):
        # cache products for self.task_dv
        if self.current_products is None:
            self.current_products = self._get_products(
                self.task_dv.data_version)

        master_query = TaskDataVersion.query.join(DataVersion).filter(
            TaskDataVersion.task_id == self.task_dv.task_id,
            DataVersion.data_type == master_type,
            TaskDataVersion.status.in_(self.MASTER_STATUSES)).order_by(
            TaskDataVersion.created_at.desc())

        #  if we don't have master data versions set current to ready
        if master_query.count() == 0:
            self.task_dv.status = const.DATA_VERSION_STATUS['ready']
            return

        for master in master_query:

            diff = self.calculate_diff(master.data_version)

            if not any(diff.values()):
                self.task_dv.status = const.DATA_VERSION_STATUS['ready']
                # if we had invalid newest data version that valid with
                # processing data version update it status to ready
                if master.status == const.DATA_VERSION_STATUS['invalid']:
                    master.status = const.DATA_VERSION_STATUS['ready']
                break

            # look up ends if we met data version with ready status
            if master.status == const.DATA_VERSION_STATUS['ready']:
                self.task_dv.status = const.DATA_VERSION_STATUS['invalid']
                self._send_report(diff, master.id)
                break
        else:
            # this means all master data versions have invalid status
            self.task_dv.status = const.DATA_VERSION_STATUS['ready']

    def calculate_diff(self, master_dv,
                       keys=('ret_sku_id', 'retsku_product_id')):
        result = {}
        master_products = self._get_products(master_dv)
        for key in keys:
            result[key] = self.current_products[key] - master_products[key]
        return result

    def _get_products(self, dv):
        data = json.loads(s3.get_content(dv.data_key))
        ret_sku_ids = set()
        retsku_product_ids = set()
        for row in data:
            if 'ret_sku_id' in row and row['ret_sku_id'] is not None:
                ret_sku_ids.add(row['ret_sku_id'])
            if ('retsku_product_id' in row and
                    row['retsku_product_id'] is not None):
                retsku_product_ids.add(row['retsku_product_id'])

        return {'ret_sku_id': ret_sku_ids,
                'retsku_product_id': retsku_product_ids}

    def _send_report(self, diff, master_id):
        message = 'Task data version {} is invalid, compared with {}.'.format(
            self.task_dv.id, master_id)
        for k, v in diff.items():
            if v:
                message += ' Missed {}: {}.'.format(k, ', '.join(map(str, v)))

        app.logger.error(message)
        if rollbar._initialized:
            rollbar.report_message(message, payload_data={
                'fingerprint': str(self.task_dv.task.id)})


class RetailerProductValidator(BaseValidator):
    """Validates retailer product data version.

    Valid condition: all ret_sku_id and retsku_product_id from price data
    are in current data version.
    """

    def validate(self):
        super().validate(const.DATA_TYPES['price'])
        db.session.commit()

    def calculate_diff(self, master_dv,
                       keys=('ret_sku_id', 'retsku_product_id')):
        result = {}
        master_products = self._get_products(master_dv)
        for key in keys:
            result[key] = master_products[key] - self.current_products[key]
        return result


class RetskuProductValidator(BaseValidator):
    """Validates retsku product data version. Retsku product is generated
    for retsku_category_id for all retailers.

    Valid condition: all price data retsku_product_id are in product.
    """

    def validate(self):
        super().validate(const.DATA_TYPES['price'])
        db.session.commit()

    def calculate_diff(self, master_dv):
        result = {}
        master_products = self._get_products(master_dv)

        key = 'retsku_product_id'
        result[key] = master_products[key] - self.current_products[key]
        return result


class PriceValidator(BaseValidator):
    """Validates price data version.

    Valid condition: all ret_sku_id and retsku_product_id are in
    retailer_product, retsku_product_id are in retsku_product data versions.
    """

    def validate(self):
        self.current_products = self._get_products(self.task_dv.data_version)

        super().validate(const.DATA_TYPES['retailer_product'])

        # check if validation with retailer_product passes
        if self.task_dv.status == const.DATA_VERSION_STATUS['invalid']:
            self._set_invalid()
            return

        super().validate(const.DATA_TYPES['retsku_product'])
        if self.task_dv.status == const.DATA_VERSION_STATUS['invalid']:
            self._set_invalid()
            return

        # apply changes
        db.session.commit()

    def _set_invalid(self):
        # do not save any changes made to master data versions
        db.session.rollback()

        self.task_dv.status = const.DATA_VERSION_STATUS['invalid']
        db.session.commit()

    def calculate_diff(self, master_dv):
        if master_dv.data_type == const.DATA_TYPES['retsku_product']:
            return super().calculate_diff(master_dv,
                                          keys=('retsku_product_id',))
        return super().calculate_diff(master_dv)


class Command(BaseCommand):

    option_list = (
        Option('--data_version_id', dest='data_version_id', type=int),)

    VALIDATORS = {
        const.DATA_TYPES['price']: PriceValidator,
        const.DATA_TYPES['retailer_product']: RetailerProductValidator,
        const.DATA_TYPES['retsku_product']: RetskuProductValidator}

    def run(self, data_version_id):
        app.logger.info('Run validate for data version {}'.format(
            data_version_id))

        data_version = DataVersion.query.get(data_version_id)
        if data_version is None:
            raise Exception('DataVersion doesn\'t exist')

        assert data_version.data_type in self.VALIDATORS

        # we should work in scope of task
        task_dv_query = TaskDataVersion.query.join(Task).filter(
            Task.deleted == False,
            TaskDataVersion.data_version_id == data_version.id)

        validator_cls = self.VALIDATORS[data_version.data_type]
        for task_dv in task_dv_query:
            validator_cls(task_dv).validate()

            if task_dv.status == const.DATA_VERSION_STATUS['ready']:
                TasksManager.update_versions(task_dv.task)


        app.logger.info('Done')
