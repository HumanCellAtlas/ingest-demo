import os
import shutil
from unittest import TestCase

from broker.service.spreadsheet_storage.spreadsheet_storage_service import SpreadsheetStorageService

TEST_STORAGE_DIR = "test_storage_dir"


class SpreadsheetStorageServiceTest(TestCase):

    def setUp(self):
        os.mkdir(TEST_STORAGE_DIR)

    def test_store_spreadsheet(self):
        test_storage_dir = "test_storage_dir"
        mock_submission_uuid = "mock-uuid"
        mock_spreadsheet_name = "mock_spreadsheet.xls"
        mock_spreadsheet_blob = bytes.fromhex('6d6f636b64617461')
        spreadsheet_storage_service = SpreadsheetStorageService(test_storage_dir)

        try:
            spreadsheet_storage_service.store(mock_submission_uuid, mock_spreadsheet_name, mock_spreadsheet_blob)
            assert True
        except Exception as e:
            assert False

    def test_retrieve_spreadsheet(self):
        test_storage_dir = "test_storage_dir"
        mock_submission_uuid = "mock-uuid"
        mock_spreadsheet_name = "mock_spreadsheet.xls"
        mock_spreadsheet_blob = bytes.fromhex('6d6f636b64617461')
        spreadsheet_storage_service = SpreadsheetStorageService(test_storage_dir)

        try:
            spreadsheet_storage_service.store(mock_submission_uuid, mock_spreadsheet_name, mock_spreadsheet_blob)
            spreadsheet = spreadsheet_storage_service.retrieve(mock_submission_uuid)
            assert spreadsheet["name"] == mock_spreadsheet_name
            assert spreadsheet["blob"] == mock_spreadsheet_blob
        except Exception as e:
            assert False

    def tearDown(self):
        shutil.rmtree(TEST_STORAGE_DIR)
