
import os
import csv

from flask.ext.script import Command as BaseCommand
from sqlalchemy.orm.exc import NoResultFound

from retsku.api.models import (db, User, Task, Assignment, Store,
                               StoreAssignment, Customer)
from retsku.api.common import retsku_api
from retsku.api.security import encrypt_password


class Command(BaseCommand):

    DATA_FILE = 'indonesia_stores.csv'
    RETAILER_NAME = 'Indonesia Telecom'
    CUSTOMER_NAME = 'Indonesia Telecom'
    PASSWORD = 'password'

    def run(self):

        retailer_id = None
        retailers = retsku_api.get_retailers()
        for retailer in retailers:
            if retailer['retailer_name'] == self.RETAILER_NAME:
                retailer_id = retailer['retailer_id']
                break

        tasks = Task.query.filter(Task.retailer_id == retailer_id).all()
        customer = Customer.query.filter(
            Customer.name == self.CUSTOMER_NAME).one()

        path = os.path.join(os.path.dirname(__file__), self.DATA_FILE)

        users = {}
        stores = {}
        assignments = {}

        with open(path, 'r') as f:
            reader = csv.DictReader(f)

            for row in reader:
                user = users.get(row['AUDITOR ID'])
                if not user:
                    try:
                        user = User.query.filter(
                            User.name == row['AUDITOR ID']).one()
                    except NoResultFound:
                        user = User(
                            name=row['AUDITOR ID'], customer=customer,
                            password=encrypt_password(self.PASSWORD))
                        db.session.add(user)
                    users[user.name] = user

                store = stores.get(row['OUTLET ID'])
                if not store:
                    try:
                        store = Store.query.filter(
                            Store.store_id == row['OUTLET ID']).one()
                    except NoResultFound:
                        store = Store(store_id=row['OUTLET ID'],
                                      retailer_id=retailer_id,
                                      country='Indonesia')
                        db.session.add(store)
                    stores[store.store_id] = store

                for task in tasks:
                    assignment = assignments.get((user.name, task.id))
                    if not assignment:
                        assignment = Assignment(task=task, user=user)
                        db.session.add(assignment)
                        assignments[(user.name, task.id)] = assignment

                    try:
                        StoreAssignment.query.filter(
                            StoreAssignment.store == store,
                            StoreAssignment.assignment == assignment).one()
                    except NoResultFound:
                        db.session.add(StoreAssignment(store=store,
                                                       assignment=assignment))
                db.session.commit()
