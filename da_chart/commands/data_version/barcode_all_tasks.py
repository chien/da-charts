
from flask.ext.script import Command as BaseCommand
from flask import current_app as app

from retsku.commands.data_version.barcode import Command as BarcodeCommand
from retsku.api.models import Task
from retsku.api import const


class Command(BaseCommand):

    def run(self):
        app.logger.info('Run create barcode pattern for all tasks')
        command = BarcodeCommand()
        for task in Task.query.filter(
                Task.task_type == const.TASK_TYPES['pattern_scan'],
                Task.deleted == False):
            command.run(task.id)
        app.logger.info('Done')
