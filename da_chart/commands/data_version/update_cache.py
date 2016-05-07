
from flask.ext.script import Command as BaseCommand

from retsku.api.models import Task
from retsku.api.managers.task import TasksManager


class Command(BaseCommand):

    def run(self):
        for task in Task.query.all():
            TasksManager.update_versions(task)
