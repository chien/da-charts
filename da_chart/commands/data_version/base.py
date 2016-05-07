
import json
from abc import ABCMeta, abstractmethod

from flask.ext.script import Command as BaseCommand, Option
from flask_restful import marshal
from flask import current_app as app

from retsku.api.models import db, Task, DataVersion, TaskDataVersion
from retsku.api.common import s3
from retsku.api import const
from retsku.api.managers.task import TasksManager


class Command(BaseCommand, metaclass=ABCMeta):

    option_list = (
        Option('--task', '-t', dest='task_id', required=True, type=int),
    )
    data_version_type = None
    json_fields = None
    need_validation = True

    def run(self, task_id, task_data_version_id=None):
        assert self.data_version_type is not None
        assert self.json_fields is not None

        app.logger.info('Run {} for task {}.'.format(self.data_version_type,
                                                     task_id))

        self.task = self.get_task(task_id)

        if task_data_version_id:
            self.task_data_version = TaskDataVersion.query.get(
                task_data_version_id)
        else:
            self.task_data_version = self.create_task_data_version(self.task)
            db.session.add(self.task_data_version)
            db.session.commit()

        # get data could need reference to data version
        self.save(self.get_data())

        status = (const.DATA_VERSION_STATUS['validating'] if
                  self.need_validation else const.DATA_VERSION_STATUS['ready'])
        self.task_data_version.status = status
        db.session.commit()

        TasksManager.update_versions(self.task)

        app.logger.info('Done. {}.'.format(
            self.task_data_version.data_version))

        return self.task_data_version.data_version.id

    def get_task(self, task_id):
        task = Task.query.get(task_id)
        if task is None:
            raise Exception('Task doesn\'t exist')
        return task

    def create_task_data_version(self, task):
        version = 0
        for data_version in TasksManager.get_latest_versions(task, False):
            if data_version.data_type == self.data_version_type:
                version = data_version.version

        version += 1
        data_version = DataVersion(
            data_type=self.data_version_type, version=version)
        data_version.data_key = self._get_data_version_key(
            task.id, self.data_version_type, version)
        data_version.data_url = s3.get_public_url(data_version.data_key)

        task_data_version = TaskDataVersion(
            task=task, data_version=data_version,
            status=const.DATA_VERSION_STATUS['processing'])

        return task_data_version

    def save(self, data):
        key = self.task_data_version.data_version.data_key
        s3.save_public_object(key, json.dumps(marshal(data, self.json_fields)))

    def _get_data_version_key(self, task_id, data_type, version):
        return '{}/{}_{}.json'.format(task_id, data_type, version)

    @abstractmethod
    def get_data(self):
        pass
