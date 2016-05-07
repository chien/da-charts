"""Generates new data versions when there is new submissions."""

from flask.ext.script import Command as BaseCommand
from flask import current_app as app

from retsku.api.models import Task, Submission, Assignment
from retsku.api.managers.task import TasksManager

from retsku.commands.data_version import display
from retsku.commands.data_version import price
from retsku.commands.data_version import retailer_product
from retsku.commands.data_version import retsku_product


class Command(BaseCommand):

    commands = [display.Command(), price.Command(), retailer_product.Command()]

    def run(self):
        app.logger.info('Run update data versions command.')

        tasks_to_update = []

        for task in Task.query.all():
            if task.deleted:
                continue

            latest_versions = TasksManager.get_latest_versions(task)
            if not latest_versions:
                continue

            newest_data_version = max(latest_versions,
                                      key=lambda x: x.updated_at)

            submissions_count = Submission.query.join(Assignment).filter(
                Assignment.task_id == task.id,
                Assignment.deleted == False,
                Submission.updated_at > newest_data_version.updated_at).count()

            if submissions_count > 0:
                tasks_to_update.append(task)

        app.logger.debug('Updating data versions for {} tasks.'.format(
            len(tasks_to_update)))
        retsku_product_command = retsku_product.Command()
        for category_id in set(
                filter(None, [t.retsku_category_id for t in tasks_to_update])):
            retsku_product_command.run(category_id)

        for task in tasks_to_update:
            for command in self.commands:
                command.run(task.id)
            TasksManager.update_versions(task)

        app.logger.info('Done.')
