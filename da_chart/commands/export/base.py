
import os
import csv
import re
from collections import OrderedDict
from copy import deepcopy
from tempfile import NamedTemporaryFile
from abc import ABCMeta, abstractmethod
from functools import reduce

from flask.ext.script import Command as BaseCommand, Option
from flask import render_template
from flask_restful import marshal

from retsku.api.common import email as email_service


class Command(BaseCommand):

    option_list = (
        Option('--email', dest='email', required=True, type=str),
        Option('--task_id', dest='task_id', type=int))

    def save_submissions(self, csv_file, submissions, output_fields):
        with open(csv_file.name, 'w') as f:
            writer = csv.DictWriter(f, fieldnames=list(output_fields.keys()))
            writer.writeheader()

            for submission in submissions:
                writer.writerow(marshal(submission, output_fields))

    def export(self, submissions, output_fields, email, subject, attach_name):
        html = render_template('email/export_submissions.html')
        csv_file = NamedTemporaryFile(delete=False)
        self.save_submissions(csv_file, submissions, output_fields)

        email_service.send_mail(email, subject, html,
                                {'name': attach_name,
                                 'filename': csv_file.name})

        os.remove(csv_file.name)


class BaseSubmissionProxy(object):
    __metaclass__ = ABCMeta

    def __init__(self, item):
        self.item = item
        self.fields_map = self.get_fields_map()
        self.name_regexp = re.compile('^({})_(\w+)_(\d+)$'.format(
            '|'.join(self.fields_map.keys())))

    def __getattr__(self, name):
        # flask restful performs some checking asking are methods available
        if name in ('strip', '__iter__'):
            raise AttributeError
        if hasattr(self.item, name):
            return getattr(self.item, name)

        match = re.match(self.name_regexp, name)
        if match:
            parent_key, child_key, index = match.groups()
            # index started with 1 so we should decrese it
            index = int(index)
            index -= 1

            parent_attr = self.fields_map.get(parent_key)
            values = reduce(getattr, parent_attr.split('.'), self.item)
            if index < len(values):
                return getattr(values[index], child_key)
            return None

        raise AttributeError

    @abstractmethod
    def get_fields_map(self):
        # return map between field prefix and sql alchemy model property name
        pass


class UnpackMixin(object):
    """Exports relationship models in flat structure."""

    def unpack_marshal_fields(self, class_fields, max_count, prefix):
        unpacked_fields = OrderedDict()
        for i in range(1, max_count + 1):
            for key in class_fields.keys():
                new_key = '{}_{}_{}'.format(prefix, key, i)
                base_field = deepcopy(class_fields[key])
                base_field.attribute = new_key
                unpacked_fields[new_key] = base_field

        return unpacked_fields
