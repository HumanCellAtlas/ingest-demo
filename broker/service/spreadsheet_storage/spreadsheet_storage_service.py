from os import path

from broker.service.spreadsheet_storage.spreadsheet_storage_exceptions import \
    SubmissionSpreadsheetDoesntExist
from .spreadsheet_storage_exceptions import SubmissionSpreadsheetAlreadyExists


class SpreadsheetStorageService:

    def __init__(self, storage_dir, storage_manifest_name="storage_manifest.json"):
        self.storage_dir = storage_dir
        self.storage_manifest_name = storage_manifest_name

    def store(self, submission_uuid, spreadsheet_blob):
        """
        Stores a given spreadsheet at path <submission_uuid>/<spreadsheetname>, local to
        the storage directory
        :param submission_uuid: the UUID for the spreadsheet submission
        :param spreadsheet_blob: spreadsheet data in bytes
        :return: the file path of the spreadsheet file in the storage
        """
        try:
            file_path = path.join(self.storage_dir, f'{submission_uuid}.xlsx')
            with open(file_path, "wb") as spreadsheet_file:
                spreadsheet_file.write(spreadsheet_blob)
                return file_path
        except FileExistsError:
            raise SubmissionSpreadsheetAlreadyExists()

    def retrieve(self, submission_uuid):
        try:
            file_path = path.join(self.storage_dir, f'{submission_uuid}.xlsx')
            file_manifest = {'name': file_path}
            with open(file_path, 'rb') as spreadsheet_file:
                data = spreadsheet_file.read()
                file_manifest['blob'] = data
            return file_manifest
        except FileNotFoundError:
            raise SubmissionSpreadsheetDoesntExist()
