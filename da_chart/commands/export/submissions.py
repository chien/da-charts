
from flask import current_app as app
from flask.ext.script import Option
from flask_restful import fields

from retsku.api.models import Submission, Assignment, Task
from retsku.api.common.formatters import format_date
from retsku.api.common.utils import class_to_marshal_fields
from retsku.commands.export.base import Command as BaseCommand


# data will be imported to CSV so fields shouldn't inculude nested fields
output_fields = {
    'GTIN': fields.String(attribute='product.gtin'),
    'Store Address': fields.String(attribute='store.address'),
    'Retailer Product Data Version ID': fields.String(
        attribute='data_version.retailer_product.id'),
    'Retailer Product Data Version URL': fields.String(
        attribute='data_version.retailer_product.data_url'),
    'Retailer Product Data Version Version': fields.String(
        attribute='data_version.retailer_product.version'),
    'Retsku Product Data Version ID': fields.String(
        attribute='data_version.retsku_product.id'),
    'Retsku Product Data Version URL': fields.String(
        attribute='data_version.retsku_product.data_url'),
    'Retsku Product Data Version Version': fields.String(
        attribute='data_version.retsku_product.version'),
    'Price Pattern Data Version ID': fields.String(
        attribute='data_version.price_pattern.id'),
    'Price Pattern Data Version URL': fields.String(
        attribute='data_version.price_pattern.data_url'),
    'Price Pattern Data Version Version': fields.String(
        attribute='data_version.price_pattern.version'),
    'Display Pattern Data Version ID': fields.String(
        attribute='data_version.display_pattern.id'),
    'Display Pattern Data Version URL': fields.String(
        attribute='data_version.display_pattern.data_url'),
    'Display Pattern Data Version Version': fields.String(
        attribute='data_version.display_pattern.version'),
    'Display Type': fields.String(attribute='display.display_type'),
    'Display Location': fields.String(attribute='display.in_store_location'),
    'Display No Of Shelves': fields.Integer(
        attribute='display.no_of_display_shelves', default=None),
    'Display No Of Facings': fields.Integer(
        attribute='display.no_of_display_facings', default=None),
    'Promotion Text': fields.String(attribute='promotion.text'),
}

output_fields.update(class_to_marshal_fields(
    Submission, exclude=['version'],
    names_map={'id': 'ID',
               'assignment_id': 'Assignment ID',
               'ret_sku_id': 'RetSKU ID',
               'store_id': 'Store ID',
               'data_version_id': 'Data Version ID',
               'display_id': 'Display ID',
               'barcode': 'Barcode',
               'raw_scanned_barcode': 'Raw Scanned Barcode',
               'store_retail_price': 'Price',
               'store_promo_price': 'Promo Price',
               'is_manual': 'Is Manual',
               'is_scanned': 'Is Scanned',
               'scanned_upc': 'Scanned UPC',
               'retsku_product_id': 'RetSKU Product ID',
               'comment': 'Comment',
               'display_damaged': 'Display Damaged',
               'not_on_shelf': 'Not On Shelf',
               'on_clearance': 'On Clearence',
               'is_end_cap': 'Is End Cap',
               'has_vignette_display': 'Has Vignette Display',
               'no_of_facing': 'No Of Facing',
               'demo_location': 'Demo Location',
               'demo_promotion': 'Demo Promotion',
               'demo_display': 'Demo Display',
               'no_of_shelves': 'No Of Shelves',
               'data_scanned_at': 'Data Scanned At',
               'data_updated_at': 'Data Updated At',
               'created_at': 'Created At',
               'updated_at': 'Updated At',
               'promotion_id': 'Promotion ID',
               'latitude': 'Latitude',
               'longitude': 'Longitude',
               'model': 'Model',
               'brand': 'Brand',
               'product_image_url': 'Product Image URL',
               'barcode_image_url': 'Barcode Image URL'}))


class Command(BaseCommand):

    option_list = (
        Option('--email', dest='email', required=True, type=str),
        Option('--task_id', dest='task_id', type=int),
        Option('--assignment_id', dest='assignment_id', type=int))

    def run(self, email, task_id=None, assignment_id=None):
        if task_id is None and assignment_id is None:
            raise Exception('Task or Assignment should be specified.')

        app.logger.info(('Run export submissions. Email: {}. Task: {}. '
                         'Assignment: {}').format(email, task_id,
                                                  assignment_id))

        if task_id:
            submissions, subject, name = self._get_task_data(task_id)
        elif assignment_id:
            submissions, subject, name = self._get_assignment_data(
                assignment_id)

        self.export(submissions, output_fields, email, subject, name)
        app.logger.info('Export done.')

    def _get_task_data(self, task_id):
        task = Task.query.get(task_id)
        submissions = Submission.query.join(Assignment).filter(
            Assignment.task_id == task_id,
            Assignment.deleted == False)
        subject = 'Submissions for {} for {}'.format(
            task.name, format_date(task.updated_at))
        name = 'Submissions_{}_{}.csv'.format(
            task.name, format_date(task.updated_at))
        return submissions, subject, name

    def _get_assignment_data(self, assignment_id):
        assignment = Assignment.query.get(assignment_id)
        submissions = Submission.query.filter(
            Submission.assignment_id == assignment_id)
        subject = 'Submissions by {} for {} for {}'.format(
            assignment.user.name, assignment.task.name,
            format_date(assignment.updated_at))
        name = 'Submissions_{}_{}_{}.csv'.format(
            assignment.user.name, assignment.task.name,
            format_date(assignment.updated_at))
        return submissions, subject, name
