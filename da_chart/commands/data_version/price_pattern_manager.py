
from collections import OrderedDict

from retsku.api.models import db, Price, PricePattern


class PricePatternWrapper(object):

    def __init__(self, task_id, in_store=True):
        self.task_id = task_id
        self.in_store = in_store
        self.prices = []

        # we need to have links to db models to get id after save
        self.pattern_obj = None

    def get_obj(self):
        if self.pattern_obj is None:
            self.pattern_obj = PricePattern()

        self.pattern_obj.task_id = self.task_id
        self.pattern_obj.in_store = self.in_store
        self.pattern_obj.prices = [p.get_obj() for p in self.prices]
        return self.pattern_obj


class PriceWrapper(object):

    def __init__(self, task_id, ret_sku_id, retsku_product_id, retail_price,
                 floor_price, no_of_facing=None, demo_location=None,
                 demo_promotion=None, demo_display=None, no_of_shelves=None,
                 **kwargs):
        # wrapper is used to generate json data file, so all serialized fields
        # should be present in instance
        self.task_id = task_id
        self.ret_sku_id = ret_sku_id
        self.retsku_product_id = retsku_product_id
        self.retail_price = retail_price
        self.floor_price = floor_price
        self.no_of_facing = no_of_facing
        self.demo_location = demo_location
        self.demo_promotion = demo_promotion
        self.demo_display = demo_display
        self.no_of_shelves = no_of_shelves

        self.in_store = None

        # we need to have links to db models to get id after save
        self.price_obj = None

    def get_obj(self):
        if self.price_obj is None:
            self.price_obj = Price()

        self.price_obj.retail_price = self.retail_price
        self.price_obj.floor_price = self.floor_price
        self.price_obj.ret_sku_id = self.ret_sku_id
        self.price_obj.retsku_product_id = self.retsku_product_id

        return self.price_obj


class PricePatternManager(object):

    def __init__(self, task):
        self.task = task

    def generate(self):
        audit_patterns = self._generate_audit_patterns()
        patterns = [p for p in audit_patterns]

        online_pattern = self._generate_online_pattern()
        if online_pattern:
            online_pattern.in_store = False
            patterns.append(online_pattern)

        for pattern in patterns:
            for price in pattern.prices:
                price.in_store = pattern.in_store

        return patterns

    def _generate_audit_patterns(self):
        # 1. for all submissions for the task that has ret_sku_id,
        # 2. group all these submission data by product and store_number
        # 3. for each store, create a price pattern,
        # 4. get the latest floor_price and retail_price from the submission
        # data and create audit_prices records for it.

        query = '''\
WITH submissions AS
(
    SELECT t.ret_sku_id, t.retsku_product_id,
        t.store_retail_price AS retail_price,
        t.store_promo_price AS floor_price, t.no_of_facing, t.demo_location,
        t.demo_promotion, t.demo_display, t.no_of_shelves, t.store_id, RANK()
    OVER (PARTITION BY t.ret_sku_id, t.store_id ORDER BY t.updated_at DESC)
    FROM audit_task_submissions AS t
    LEFT JOIN audit_assignments AS a ON t.audit_assignment_id = a.id
    WHERE a.audit_task_id = {} AND t.ret_sku_id IS NOT NULL
)
SELECT * FROM submissions WHERE rank = 1;
'''.format(self.task.id)

        patterns = OrderedDict()
        for price_data in db.engine.execute(query):
            store_id = price_data['store_id']

            if store_id not in patterns:
                patterns[store_id] = PricePatternWrapper(self.task.id)
            pattern = patterns[store_id]

            pattern.prices.append(PriceWrapper(self.task.id, **price_data))

        return patterns.values()

    def _generate_online_pattern(self):
        # for all retailer_products, get the latest retail price and promo
        # price to create price pattern
        if (self.task.retailer_id is None or
           self.task.retsku_category_id is None):
            return

        query = '''\
WITH prices AS
(
    SELECT prod.ret_sku_id, prod.retsku_product_id,
        prices.regular_price AS retail_price,
        prices.product_price AS floor_price, RANK()
    OVER (PARTITION BY prices.ret_sku_id ORDER BY prices.updated_at DESC)
    FROM product_prices AS prices
    LEFT JOIN products_universal AS prod ON prices.ret_sku_id = prod.ret_sku_id
    WHERE prod.retailer_id = {} AND prod.retsku_category_id = {}
)
SELECT * FROM prices WHERE rank = 1 ORDER BY ret_sku_id;
'''.format(self.task.retailer_id, self.task.retsku_category_id)

        result = db.engine.execute(query)
        if not result.rowcount:
            return

        pattern = PricePatternWrapper(self.task.id)

        for price_data in result:
            pattern.prices.append(PriceWrapper(self.task.id, **price_data))

        return pattern
