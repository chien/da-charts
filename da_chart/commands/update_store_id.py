
from flask.ext.script import Command as BaseCommand
from flask import current_app as app

from retsku.api.models import db, Submission
from retsku.api.managers.store import StoreManager
from retsku.api.managers.submission import SubmissionManager


class Command(BaseCommand):

    def run(self):
        app.logger.info('Run update store number command.')
        for sub in Submission.query.filter(
            Submission.latitude != None, Submission.longitude != None,
            Submission.store_id == None):

            if (sub.latitude == '' or sub.longitude == ''):
                continue

            try:
                lat, lon = float(sub.latitude), float(sub.longitude)
            except ValueError:
                continue

            retailer_id = SubmissionManager.get_retailer_id(sub)

            nearest = StoreManager.find_nearest(lat, lon,
                                                retailer_id).fetchone()
            if nearest:
                app.logger.debug('Update submission {} with store {}.'.format(
                                 sub.id, nearest[0]))
                sub.store_id = nearest[0]

        db.session.commit()
        app.logger.info('Done.')
