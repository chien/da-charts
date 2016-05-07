
import json

from flask.ext.script import Command as BaseCommand, Option
from flask import current_app as app

from retsku.api.models import db, Customer, Settings


class Command(BaseCommand):

    option_list = (
        Option('--name', '-n', dest='name', required=True, type=str),
        Option('--settings', '-s', dest='settings_json', type=json.loads))

    def run(self, name, settings_json=None):
        customer = Customer(name=name)
        customer.settings = Settings(settings=settings_json)

        db.session.add(customer)
        db.session.commit()

        app.logger.info('Customer has been created. {}. {}'.format(
            customer, customer.settings))
