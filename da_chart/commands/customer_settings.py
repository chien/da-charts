
import json

from flask.ext.script import Command as BaseCommand, Option
from flask import current_app as app

from retsku.api.models import db, Customer, Settings


class Command(BaseCommand):
    """
        - show: print customer's settings
        - create: create settings for customer without them
        - update: change customer's settings with new values
        - merge: update customer's settings with new values
    """

    option_list = (
        Option('--customer', '-i', dest='customer_id', required=True,
               type=int),
        Option('--command', '-c', dest='command',
               choices=['show', 'create', 'update', 'merge'], default='show'),
        Option('--settings', '-s', dest='settings_json', type=json.loads))

    def run(self, customer_id, command, settings_json=None):
        customer = Customer.query.get(customer_id)
        if customer is None:
            raise Exception('Customer doesn\'t exist')

        if command == 'show':
            app.logger.info(customer.settings)
        elif command == 'create':
            if customer.settings is not None:
                raise Exception('Customer settings already existed')
            customer.settings = Settings(settings=settings_json)
            db.session.add(customer)
            db.session.commit()
            app.logger.info('Settings has been created. {}.'.format(
                customer.settings))
        elif command == 'update':
            if customer.settings is None:
                raise Exception('Customer settings doesn\'t exist')
            customer.settings.settings = settings_json
            db.session.commit()
            app.logger.info('Settings has been updated. {}.'.format(
                customer.settings))
        elif command == 'merge':
            if customer.settings is None:
                raise Exception('Customer settings doesn\'t exist')
            customer.settings.settings.update(settings_json)
            db.session.commit()
            app.logger.info('Settings has been merged. {}.'.format(
                customer.settings))
