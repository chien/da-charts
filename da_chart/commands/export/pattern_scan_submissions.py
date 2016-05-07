
from flask import current_app as app
from flask_restful import fields

from retsku.api.models import (PatternScanSubmission, PatternScanSubmissionURL,
                               Assignment, Task)
from retsku.api.common.formatters import format_date
from retsku.api.common.utils import class_to_marshal_fields
from retsku.commands.export.base import (BaseSubmissionProxy, UnpackMixin,
                                         Command as BaseCommand)


# data will be imported to CSV so fields shouldn't inculude nested fields
output_fields = class_to_marshal_fields(PatternScanSubmission)
output_fields['task_name'] = fields.String(attribute='assignment.task.name')
output_fields['task_id'] = fields.Integer(attribute='assignment.task.id')
output_fields['user_id'] = fields.Integer(attribute='assignment.user.id')
output_fields['user_name'] = fields.String(attribute='assignment.user.name')
output_fields['assignment_id'] = fields.Integer(attribute='assignment_id')


url_fields = class_to_marshal_fields(
    PatternScanSubmissionURL, exclude=['submission_id', 'updated_at',
                                       'created_at'])


class SubmissionProxy(BaseSubmissionProxy):

    BARCODE = 'barcode_url'
    PACKAGE = 'package_url'

    def get_fields_map(self):
        return {self.BARCODE: 'barcode_urls',
                self.PACKAGE: 'package_urls'}


class Command(BaseCommand, UnpackMixin):

    def run(self, email, task_id):
        app.logger.info(
            'Run export pattern scan submissions. Email: {}. Task: {}.'.format(
                email, task_id))
        submissions, subject, name = self._get_task_data(task_id)
        if submissions:
            max_barcode_count = max((len(s.barcode_urls) for s in submissions))
            max_package_count = max((len(s.package_urls) for s in submissions))
        else:
            max_barcode_count = 0
            max_package_count = 0

        unpacked_fields = output_fields.copy()
        unpacked_fields.update(self.unpack_marshal_fields(
            url_fields, max_barcode_count, SubmissionProxy.BARCODE))
        unpacked_fields.update(self.unpack_marshal_fields(
            url_fields, max_package_count, SubmissionProxy.PACKAGE))

        submissions = [SubmissionProxy(s) for s in submissions]
        self.export(submissions, unpacked_fields, email, subject, name)
        app.logger.info('Export done.')

    def _get_task_data(self, task_id):
        task = Task.query.get(task_id)
        submissions = PatternScanSubmission.query.join(Assignment).filter(
            Assignment.task_id == task_id,
            Assignment.deleted == False).all()
        subject = 'Pattern scan submissions for {} for {}'.format(
            task.name, format_date(task.updated_at))
        name = 'pattern_scan_submissions_{}_{}.csv'.format(
            task.name, format_date(task.updated_at))
        return submissions, subject, name
