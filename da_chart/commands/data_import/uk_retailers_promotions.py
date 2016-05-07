
from flask.ext.script import Command as BaseCommand

from retsku.api.models import db, Promotion
from retsku.api.common import retsku_api


PROMOTIONS = [
    ('Tesco', 'Any 2 for $'),
    ('Tesco', 'Any 3 for $'),
    ('Tesco', 'Any 4 for $'),
    ('Tesco', 'Any 5 for $'),
    ('Tesco', 'Any 6 for $'),
    ('Tesco', 'Any 7 for $'),
    ('Tesco', 'Any 8 for $'),
    ('Tesco', 'Any 9 for $'),
    ('Tesco', 'Any 10 for $'),
    ('Tesco', 'Better than half price'),
    ('Tesco', 'Half price'),
    ('Tesco', 'Save $ Was $ Now $'),
    ('Tesco', 'Special Purchase'),
    ('Tesco', 'Only $'),
    ('Tesco', 'Any # for # Cheapest Product FREE'),
    ('Sainsbury\'s', 'Half price'),
    ('Sainsbury\'s', 'Only $: Save $'),
    ('Sainsbury\'s', 'Save % Was $ Now $'),
    ('Waitrose', '% Off'),
    ('Waitrose', 'Buy 1 and 2nd half price '),
    ('Waitrose', '# for $'),
    ('Waitrose', 'Only $'),
    ('Waitrose', 'Save % Was $ Now $'),
    ('Waitrose', 'Mix & Match Add # for # Cheapest Product FREE'),
    ('Waitrose', 'Any 2 for $'),
    ('Waitrose', 'Any 3 for $'),
    ('Waitrose', 'Any 4 for $'),
    ('Waitrose', 'Any 5 for $'),
    ('Waitrose', 'Any 6 for $'),
    ('Waitrose', 'Any 7 for $'),
    ('Waitrose', 'Any 8 for $'),
    ('Waitrose', 'Any 9 for $'),
    ('Waitrose', 'Any 10 for $'),
    ('Waitrose', 'Add 2 get 2nd half price (cheap item half price),'),
    ('ASDA', 'Rollback'),
    ('ASDA', 'Any 2 for $'),
    ('ASDA', 'Any 3 for $'),
    ('ASDA', 'Any 4 for $'),
    ('ASDA', 'Any 5 for $'),
    ('ASDA', 'Any 6 for $'),
    ('ASDA', 'Any 7 for $'),
    ('ASDA', 'Any 8 for $'),
    ('ASDA', 'Any 9 for $'),
    ('ASDA', 'Any 10 for $'),
    ('Iceland', 'Any 2 for $'),
    ('Iceland', 'Any 3 for $'),
    ('Iceland', 'Any 4 for $'),
    ('Iceland', 'Any 5 for $'),
    ('Iceland', 'Any 6 for $'),
    ('Iceland', 'Any 7 for $'),
    ('Iceland', 'Any 8 for $'),
    ('Iceland', 'Any 9 for $'),
    ('Iceland', 'Any 10 for $'),
    ('Iceland', 'Was $ Save $')]


class Command(BaseCommand):

    def run(self):
        retailers = retsku_api.get_retailers()
        for retailer, promo in PROMOTIONS:
            retailer_id = self._get_retailer_id(retailers, retailer)
            promotion = Promotion(text=promo, retailer_id=retailer_id)
            db.session.add(promotion)

        db.session.commit()

    def _get_retailer_id(self, retailers, name):
        for retailer in retailers:
            if retailer['retailer_name'] == name:
                return int(retailer['retailer_id'])
