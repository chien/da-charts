
from flask.ext.script import Manager

from retsku.api.app import create_app

from retsku.commands import update_store_id
from retsku.commands import create_customer
from retsku.commands import customer_settings
from retsku.commands.data_version import price
from retsku.commands.data_version import retailer_product
from retsku.commands.data_version import display
from retsku.commands.data_version import update_cache
from retsku.commands.data_version import retsku_product
from retsku.commands.data_version import barcode
from retsku.commands.data_version import barcode_all_tasks
from retsku.commands.data_version import update_data_versions
from retsku.commands.data_version import validate
from retsku.commands.export import submissions
from retsku.commands.export import pop_submissions
from retsku.commands import create_missing_products
from retsku.commands import update_submissions_product
from retsku.commands import link_missing_products
from retsku.commands.data_import import check_missing_pattern
from retsku.commands import create_pattern_scan_products
from retsku.commands.data_import import uk_retailers_promotions
from retsku.commands.data_import import indonesia_stores_assignments
import retsku.commands.data_migrations as data_migrations


manager = Manager(create_app())
manager.add_command('update-store-id', update_store_id.Command())
manager.add_command('create-price-data-version', price.Command())
manager.add_command('create-retailer-data-version', retailer_product.Command())
manager.add_command('create-diplay-data-version', display.Command())
manager.add_command('create-product-data-version', retsku_product.Command())
manager.add_command('create-barcode-data-version', barcode.Command())
manager.add_command('create-barcode-data-version-all-tasks',
                    barcode_all_tasks.Command())
manager.add_command('update-data-version-cache', update_cache.Command())
manager.add_command('update-data-versions', update_data_versions.Command())
manager.add_command('update-data-versions', update_data_versions.Command())
manager.add_command('validate-data-versions', validate.Command())
manager.add_command('create-customer', create_customer.Command())
manager.add_command('customer-settings', customer_settings.Command())
manager.add_command('export-submissions', submissions.Command())
manager.add_command('export-pop-submissions', pop_submissions.Command())
manager.add_command('create-missing-products',
                    create_missing_products.Command())
manager.add_command('update-submissions-product',
                    update_submissions_product.Command())
manager.add_command('create-pattern-scan-products',
                    create_pattern_scan_products.Command())
manager.add_command('link-missing-products',
                    link_missing_products.Command())
manager.add_command('check-indosat-patterns',
                    check_missing_pattern.Command())
manager.add_command('import-uk-promotions',
                    uk_retailers_promotions.Command())
manager.add_command('import-indonesia-stores',
                    indonesia_stores_assignments.Command())

# data migrations
manager.add_command('update-pop-submissions-indexes',
                    data_migrations.update_pop_submissions_indexes.Command())


if __name__ == '__main__':
    manager.run()
