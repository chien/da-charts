
from retsku.api.app import celery

from retsku.commands.data_version import (price, retailer_product, display,
                                          validate, barcode)
from retsku.commands.export import (submissions, pop_submissions,
                                    pattern_scan_submissions)


@celery.task
def generate_price_patterns(task_id, task_data_version_id):
    command = price.Command()
    return command.run(task_id, task_data_version_id)


@celery.task
def generate_retailer_products(task_id, task_data_version_id):
    command = retailer_product.Command()
    return command.run(task_id, task_data_version_id)


@celery.task
def generate_display_patterns(task_id, task_data_version_id):
    command = display.Command()
    return command.run(task_id, task_data_version_id)


@celery.task
def generate_barcode_patterns(task_id, task_data_version_id):
    command = barcode.Command()
    return command.run(task_id, task_data_version_id)


@celery.task
def export_submissions(email, task_id, assignment_id=None):
    command = submissions.Command()
    command.run(email, task_id, assignment_id)


@celery.task
def export_pop_submissions(email, task_id):
    command = pop_submissions.Command()
    command.run(email, task_id)


@celery.task
def export_pattern_scan_submissions(email, task_id):
    command = pattern_scan_submissions.Command()
    command.run(email, task_id)


@celery.task(name='validate_data_version')
def validate_data_version(data_version_id):
    command = validate.Command()
    command.run(data_version_id)
