
from flask.ext.script import Command as BaseCommand

from retsku.api.models import db
from retsku.api.pop_models import POPSubmission


class Command(BaseCommand):

    def run(self):
        for submission in POPSubmission.query.all():
            index = 0
            for image in submission.images:
                image.index = index
                index += 1

            index = 0
            for provider in submission.providers:
                provider.index = index
                index += 1

        db.session.commit()
