import os
from os import path
from tempfile import TemporaryDirectory
from tempfile import TemporaryFile
from unittest import TestCase

from broker.service.spreadsheet_storage.spreadsheet_storage_exceptions import \
    SubmissionSpreadsheetDoesntExist
from broker.service.spreadsheet_storage.spreadsheet_storage_service import SpreadsheetStorageService


class _TestFile:

    def __init__(self, delegate_file: TemporaryFile):
        self.delegate_file = delegate_file

    def write(self, data):
        """
        Convenience utility so that the call to seek can be hidden.
        """
        self.delegate_file.write(data)
        self.delegate_file.seek(0)


def _as_test_file(test_file):
    return _TestFile(test_file)


class _TestDirectory:

    def __init__(self, directory_path):
        self.directory_path = directory_path

    def list_files(self, ends_with=None):
        if path.isdir(self.directory_path):
            files = os.listdir(self.directory_path)
            if ends_with:
                files = list(filter(lambda file: file.endswith(ends_with), files))
            return files
        else:
            raise RuntimeError(f'{self.directory_path} is not a directory')


def _as_test_dir(test_directory):
    return _TestDirectory(test_directory)


class SpreadsheetStorageServiceTest(TestCase):

    def test_store_spreadsheet(self):
        with TemporaryDirectory() as storage_root:
            # given:
            spreadsheet_storage_service = SpreadsheetStorageService(storage_root)

            # and:
            submission_uuid = "78451f36-c782-4d2d-8491-47e06ddb860f"
            spreadsheet_data = b'spreadsheet_data'

            # when:
            file_path = spreadsheet_storage_service.store(submission_uuid, spreadsheet_data)

            # then:
            excel_files = _as_test_dir(storage_root).list_files(ends_with='.xlsx')
            self.assertEqual(1, len(excel_files))
            with open(file_path, 'rb') as stored_file:
                self.assertEqual(stored_file.readline(), spreadsheet_data)

    def test_store_updated_spreadsheet(self):
        with TemporaryDirectory() as storage_root:
            # given:
            storage = SpreadsheetStorageService(storage_root)
            submission_uuid = '44858abe-3d6a-4e86-aeed-0eb5891da6cf'
            storage.store(submission_uuid, b'spreadsheet')

            # and: assume file is stored
            spreadsheet_directory = _as_test_dir(storage_root)
            self.assertEqual(1, len(spreadsheet_directory.list_files(ends_with='.xlsx')))

            # when: upload the same file again
            updated_data = b'updated_spreadsheet'
            file_path = storage.store(submission_uuid, updated_data)

            # then:
            with open(file_path, 'rb') as stored_file:
                self.assertEqual(stored_file.readline(), updated_data)

    def test_retrieve_spreadsheet(self):
        with TemporaryDirectory() as storage_dir:
            # given: test file in the storage directory
            submission_uuid = "8e9602a9-b619-4593-ae68-3cc0f2cdf729"
            file_path = path.join(storage_dir, f'{submission_uuid}.xlsx')
            spreadsheet_data = b'spreadsheet_data'
            with open(file_path, 'wb') as stored_file:
                stored_file.write(spreadsheet_data)

            # and:
            storage = SpreadsheetStorageService(storage_dir)

            # when:
            file_manifest = storage.retrieve(submission_uuid)

            # then:
            self.assertEqual(file_path, file_manifest.get('name'))
            self.assertEqual(spreadsheet_data, file_manifest.get('blob'))

    def test_retrieve_non_existent_spreadsheet(self):
        with TemporaryDirectory() as storage_dir:
            # given:
            storage = SpreadsheetStorageService(storage_dir)

            # expect:
            self.assertRaises(SubmissionSpreadsheetDoesntExist, storage.retrieve,
                              'd99bf112-b10c-450d-97d7-5359a31065b5')
