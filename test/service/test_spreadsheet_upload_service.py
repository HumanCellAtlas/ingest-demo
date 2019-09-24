from unittest import TestCase

from mock import Mock, patch

from broker.service.spreadsheet_upload_service import SpreadsheetUploadService


class SpreadsheetUploadServiceTest(TestCase):

    def setUp(self) -> None:
        self.ingest_api = Mock('ingest_api')
        self.storage_service = Mock('storage_service')
        self.importer = Mock('importer')

    @patch('broker.service.spreadsheet_upload_service.secure_filename')
    @patch('broker.service.spreadsheet_upload_service.XlsImporter')
    def test_upload_success(self, mock_importer, mock_secure_filename):
        # given:
        mock_importer.create_update_spreadsheet = Mock()
        spreadsheet_upload_service = SpreadsheetUploadService(self.ingest_api, self.storage_service, self.importer)
        submission_resource = {
            'uuid': {'uuid': 'submission-uuid'},
            '_links': {
                'self': {
                    'href': 'url'
                }
            },
            'isUpdate': False
        }
        request_file = Mock()
        request_file.read = Mock(return_value='content')
        request_file.filename = 'filename'

        mock_secure_filename.return_value = 'secure-filename'

        self.storage_service.store = Mock(return_value='path')
        mock_submission = Mock('submission')
        mock_template_mgr = Mock('template_mgr')
        self.importer.import_file = Mock(return_value=(mock_submission, mock_template_mgr))

        # when
        output = spreadsheet_upload_service._upload(submission_resource, request_file)

        # then
        mock_secure_filename.assert_called_once_with('filename')
        self.storage_service.store.assert_called_once_with('submission-uuid', 'secure-filename', 'content')

        self.importer.import_file('path', 'url', None)

        mock_importer.create_update_spreadsheet.assert_called_with(mock_submission, mock_template_mgr, 'path')

        self.assertEqual(output.submission, mock_submission)
        self.assertEqual(output.template_manager, mock_template_mgr)
        self.assertEqual(output.path, 'path')

    @patch('broker.service.spreadsheet_upload_service.secure_filename')
    @patch('broker.service.spreadsheet_upload_service.XlsImporter')
    def test_upload_update_success(self, mock_importer, mock_secure_filename):
        # given:
        mock_importer.create_update_spreadsheet = Mock()
        spreadsheet_upload_service = SpreadsheetUploadService(self.ingest_api, self.storage_service, self.importer)
        submission_resource = {
            'uuid': {'uuid': 'submission-uuid'},
            '_links': {
                'self': {
                    'href': 'url'
                }
            },
            'isUpdate': True
        }
        request_file = Mock()
        request_file.read = Mock(return_value='content')
        request_file.filename = 'filename'

        mock_secure_filename.return_value = 'secure-filename'

        self.storage_service.store = Mock(return_value='path')
        mock_submission = Mock('submission')
        mock_template_mgr = Mock('template_mgr')
        self.importer.import_file = Mock(return_value=(mock_submission, mock_template_mgr))

        # when
        output = spreadsheet_upload_service._upload(submission_resource, request_file)

        # then
        mock_secure_filename.assert_called_once_with('filename')
        self.storage_service.store.assert_called_once_with('submission-uuid', 'secure-filename', 'content')

        self.importer.import_file('path', 'url', None)
        mock_importer.create_update_spreadsheet.assert_called_with(mock_submission, mock_template_mgr, 'path')

        self.assertEqual(output.submission, mock_submission)
        self.assertEqual(output.template_manager, mock_template_mgr)
        self.assertEqual(output.path, 'path')
