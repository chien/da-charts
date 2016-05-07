import csv
import os
import re

from flask.ext.script import Command as BaseCommand

class Command(BaseCommand):
    DATA_FILE = 'indosat_patterns.csv'
    DATA_BARCODE_FILE = 'indosat_barcodes.csv'

    def run(self):
        path = os.path.join(os.path.dirname(__file__), self.DATA_FILE)

        patterns = []

        with open(path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                patterns.append({ "pattern": row['pattern'], 'brand': row['brand'], 'model': row['model']})

        barcode_path = os.path.join(os.path.dirname(__file__), self.DATA_BARCODE_FILE)

        all_barcode_count = 0
        match_barcode_count = 0
        unmatch_barcode_count = 0

        with open(barcode_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                all_barcode_count += 1
                for pattern in patterns:
                    m = re.search(pattern['pattern'], row['barcode'].replace("'",""))
                    if m:
                        match_barcode_count += 1
                        # print("Match: {brand} {model} barcode: {barcode} with {pattern}".format(brand=pattern['brand'], model=pattern['model'], barcode=row['barcode'], pattern=pattern['pattern']))
                        break
                else:
                    unmatch_barcode_count += 1
                    print("******* Not Match: brand: {brand}, model: {model}, barcode: {barcode} - retsku product id: {retsku_product_id}".format(
                        barcode=row['barcode'],
                        brand=row['brand'],
                        model=row['model'],
                        retsku_product_id=row['retsku_product_id']))

        print("Total: {}, Match: {}, Not Match: {}".format(all_barcode_count,match_barcode_count,unmatch_barcode_count))
