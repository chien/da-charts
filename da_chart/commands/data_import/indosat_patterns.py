
import csv
import os
from flask.ext.script import Command as BaseCommand

from retsku.api.models import db, Product, Brand, BarcodePattern, Task


class Command(BaseCommand):

    DATA_FILE = 'indosat_patterns.csv'
    DUMMY = 'dummy'
    TASK_NAME = 'Indonesia Telecom Barcode'

    def run(self):

        task = Task.query.filter(Task.name == self.TASK_NAME).first()
        if not task:
            task = Task(name=self.TASK_NAME)
            db.session.add(task)
            db.session.commit()

        path = os.path.join(os.path.dirname(__file__), self.DATA_FILE)

        with open(path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                brand_name = row['brand'].lower()
                brand = Brand.query.filter(
                    Brand.brand_name == brand_name).first()
                if not brand:
                    brand = Brand(brand_name=brand_name)
                    db.session.add(brand)
                    db.session.commit()

                product = Product.query.filter(
                    Product.retailer_id==row['retailer_id'],
                    Product.retsku_product_id==row['retsku_product_id']).first()
                if not product:
                    product = Product(
                        brand=brand,
                        model_name=row['model'],
                        external_product_code=row['retsku_product_id'],
                        retsku_product_id=row['retsku_product_id'],
                        retsku_category_id=row['retsku_category_id'],
                        retailer_id=row['retailer_id'])
                    db.session.add(product)

                pattern = BarcodePattern(product=product,
                                         task=task,
                                         pattern=row['pattern'] or self.DUMMY)
                db.session.add(pattern)
            db.session.commit()
