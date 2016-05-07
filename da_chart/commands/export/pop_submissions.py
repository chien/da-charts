
from collections import OrderedDict

from flask import current_app as app
from flask_restful import fields

from retsku.api.pop_models import POPSubmission, POPSubmissionProvider
from retsku.api.models import db, Task
from retsku.api.common.formatters import format_date
from retsku.api.common.utils import class_to_marshal_fields
from retsku.commands.export.base import Command as BaseCommand


# data will be imported to CSV so fields shouldn't include nested fields
provider_fields = class_to_marshal_fields(POPSubmissionProvider)
output_fields = OrderedDict()
for k, v in provider_fields.items():
    key = 'pop_provider_{}'.format(k) if k != 'submission_id' else k
    v.attribute = key
    output_fields[key] = v

submission_fields = class_to_marshal_fields(
    POPSubmission, exclude=['id', 'updated_at', 'created_at'])
output_fields.update(submission_fields)

output_fields['task_id'] = fields.Integer
output_fields['task_name'] = fields.String
output_fields['user_id'] = fields.Integer
output_fields['user_name'] = fields.String
output_fields['customer_id'] = fields.Integer(default=None)
output_fields['customer_name'] = fields.String

output_fields['pop_provider_promotion_name'] = fields.String
output_fields['pop_provider_provider_name'] = fields.String

output_fields['pop_image_id'] = fields.Integer(default=None)
output_fields['pop_image_url'] = fields.String


class Command(BaseCommand):

    def run(self, email, task_id):
        app.logger.info(
            'Run export pop submissions. Email: {}. Task: {}.'.format(
                email, task_id))
        providers, subject, name = self._get_task_data(task_id)

        self.export(providers, output_fields, email, subject, name)
        app.logger.info('Export done.')

    def _get_task_data(self, task_id):
        task = Task.query.get(task_id)

        query = '''
SELECT p.id as pop_provider_id, p.provider_name as pop_provider_name,
    p.pop_task_ad_type_id as pop_provider_ad_type_id,
    p.pop_task_promotion_id as pop_provider_promotion_id,
    p.pop_task_provider_id as pop_provider_provider_id,
    p.description as pop_provider_description,
    p.ad_type as pop_provider_ad_type, p.quantity as pop_provider_quantity,
    p.index as pop_provider_index, p.created_at as pop_provider_created_at,
    p.updated_at as pop_provider_updated_at,
    s.id as submission_id, s.store_name, s.store_address, s.store_id,
    s.latitude, s.longitude, s.data_scanned_at, s.data_updated_at, s.version,
    t.id as task_id, t.name as task_name,
    u.id as user_id, u.name as user_name,
    c.id as customer_id, c.name as customer_name,
    i.id as pop_image_id, i.s3_url as pop_image_url,
    promo.name as pop_provider_promotion_name,
    provider.name as pop_provider_provider_name
FROM pop_task_provider_submissions AS p
    LEFT JOIN pop_task_submissions AS s ON p.pop_task_submission_id = s.id
    LEFT JOIN audit_assignments AS a ON s.audit_assignment_id = a.id
    LEFT JOIN audit_tasks AS t ON a.audit_task_id = t.id
    LEFT JOIN audit_users AS u ON a.audit_user_id = u.id
    LEFT JOIN audit_customers AS c on u.audit_customer_id = c.id
    LEFT JOIN pop_task_images AS i on
        p.pop_task_submission_id = i.pop_task_submission_id AND
        p.index = i.index
    LEFT JOIN pop_task_promotions AS promo ON
        p.pop_task_promotion_id = promo.id
    LEFT JOIN pop_task_providers AS provider ON
        p.pop_task_provider_id = provider.id
WHERE
    t.id = {} AND t.deleted = False AND a.deleted = False
ORDER BY
    p.id;
'''.format(task_id)

        providers = db.engine.execute(query).fetchall()

        subject = 'POP submissions for {} for {}'.format(
            task.name, format_date(task.updated_at))
        name = 'pop_submissions_{}_{}.csv'.format(
            task.name, format_date(task.updated_at))
        name = name.replace(' ', '_').lower()
        return providers, subject, name
