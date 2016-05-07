
from flask_restful import fields

from retsku.api.models import db, Display
from retsku.api import const
from retsku.commands.data_version.base import Command as BaseCommand
from retsku.api.common.utils import class_to_marshal_fields


class Command(BaseCommand):

    json_fields = {
        'ret_sku_id': fields.Integer(default=None),
        'retsku_product_id': fields.Integer(default=None)}
    json_fields.update(class_to_marshal_fields(
        Display, exclude=['latitude', 'longitude', 'updated_at',
                          'created_at', 'parent_id']))

    data_version_type = const.DATA_TYPES['display']

    def get_data(self):
        # we should keep in mind query and Display model fields synchronization
        query = '''\
SELECT s.ret_sku_id, s.retsku_product_id, d.id, d.store_id,
    d.external_display_id, display_type, d.in_store_location,
    d.no_of_display_shelves, d.no_of_display_facings, d.image_url
    FROM audit_task_submissions AS s
    LEFT JOIN audit_assignments AS a ON s.audit_assignment_id = a.id
    LEFT JOIN displays as d ON s.display_id = d.id
    WHERE s.display_id IS NOT NULL and a.audit_task_id = {}
    ORDER BY s.id;
'''.format(self.task.id)
        return db.engine.execute(query).fetchall()
