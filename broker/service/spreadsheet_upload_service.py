import logging
from collections import namedtuple

from ingest.api.ingestapi import IngestApi
from ingest.importer.importer import XlsImporter
from werkzeug.utils import secure_filename

from broker.service.spreadsheet_storage.spreadsheet_storage_service import SpreadsheetStorageService

SpreadsheetUploadOutput = namedtuple('SpreadsheetUploadOutput', 'submission template_manager path')


class SpreadsheetUploadService:
    def __init__(self, ingest_api: IngestApi, storage_service: SpreadsheetStorageService, importer: XlsImporter):
        self.ingest_api = ingest_api
        self.storage_service = storage_service
        self.importer = importer
        self.logger = logging.getLogger(__name__)

    def upload(self, submission_resource, request_file, project_uuid=None) -> SpreadsheetUploadOutput:
        self.logger.info('Spreadsheet upload started!')
        submission_url = submission_resource["_links"]["self"]["href"].rsplit("{")[0]
        submission_uuid = submission_resource["uuid"]["uuid"]
        filename = secure_filename(request_file.filename)
        path = self.storage_service.store(submission_uuid, filename, request_file.read())
        submission, template_manager = self.importer.import_file(path, submission_url, project_uuid)
        XlsImporter.create_update_spreadsheet(submission, template_manager, path)
        self.logger.info('Spreadsheet upload done!')
        return SpreadsheetUploadOutput(submission=submission, template_manager=template_manager, path=path)
