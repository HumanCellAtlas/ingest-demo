#!/usr/bin/env python
import sys

from ingest.importer.spreadsheetUploadError import SpreadsheetUploadError

__author__ = "jupp"
__license__ = "Apache 2.0"

from flask import Flask, flash, request, render_template, redirect, url_for, send_file
from flask_cors import CORS, cross_origin
from flask import json
from ingest.api.ingestapi import IngestApi
from ingest.importer.importer import XlsImporter
from broker.service.summary_service import SummaryService
from broker.service.spreadsheet_storage.spreadsheet_storage_service import SpreadsheetStorageService
from broker.service.spreadsheet_storage.spreadsheet_storage_exceptions import SubmissionSpreadsheetDoesntExist

from werkzeug.utils import secure_filename
import os
import io
import threading
import logging
import traceback
import jsonpickle

STATUS_LABEL = {
    'Valid': 'label-success',
    'Validating': 'label-info',
    'Invalid': 'label-danger',
    'Submitted': 'label-default',
    'Complete': 'label-default'
}

DEFAULT_STATUS_LABEL = 'label-warning'

HTML_HELPER = {
    'status_label': STATUS_LABEL,
    'default_status_label': DEFAULT_STATUS_LABEL
}

logging.getLogger('ingest').setLevel(logging.INFO)
logging.getLogger('ingest.api.ingestapi').setLevel(logging.DEBUG)

format = ' %(asctime)s  - %(name)s - %(levelname)s in %(filename)s:' \
         '%(lineno)s %(funcName)s(): %(message)s'
logging.basicConfig(stream=sys.stdout, level=logging.INFO,
                    format=format)

logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static')
app.secret_key = 'cells'
cors = CORS(app, expose_headers=["Content-Disposition"])
app.config['CORS_HEADERS'] = 'Content-Type'

SPREADSHEET_STORAGE_DIR = os.environ.get('SPREADSHEET_STORAGE_DIR')


@app.route('/', methods=['GET'])
def index():
    new_ui_url = os.environ['INGEST_UI']
    if new_ui_url:
        return redirect(new_ui_url, code=302)

    return json.dumps({'message': "Ingest Broker API is running!"}), 200, {'ContentType': 'application/json'}


@app.route('/api_upload', methods=['POST'])
@cross_origin()
def upload_spreadsheet():
    return _upload_spreadsheet()


@app.route('/api_upload_update', methods=['POST'])
@cross_origin()
def upload_update_spreadsheet():
    return _upload_spreadsheet(True)


def _upload_spreadsheet(update=False):
    try:
        logger.info("Uploading spreadsheet")
        token = _check_token()

        ingest_api = IngestApi()
        ingest_api.set_token(token)
        importer = XlsImporter(ingest_api)

        project = _check_for_project(ingest_api)

        project_uuid = None
        if project and project.get('uuid'):
            project_uuid = project.get('uuid').get('uuid')

        submission = ingest_api.create_submission(update)
        submission_url = submission["_links"]["self"]["href"].rsplit("{")[0]
        submission_uuid = submission["uuid"]["uuid"]
        path = _save_spreadsheet(submission_uuid)

        _submit_spreadsheet_data(importer, path, submission_url, project_uuid)

        return create_upload_success_response(submission_url)
    except SpreadsheetUploadError as spreadsheetUploadError:
        return create_upload_failure_response(spreadsheetUploadError.http_code,
                                              spreadsheetUploadError.message,
                                              spreadsheetUploadError.details)
    except Exception as err:
        logger.error(traceback.format_exc())
        return create_upload_failure_response(500,
                                              "We experienced a problem while uploading your spreadsheet",
                                              str(err))


@app.route('/submissions/<submission_uuid>/summary', methods=['GET'])
def submission_summary(submission_uuid):
    submission = IngestApi().get_submission_by_uuid(submission_uuid)
    summary = SummaryService().summary_for_submission(submission)

    return app.response_class(
        response=jsonpickle.encode(summary, unpicklable=False),
        status=200,
        mimetype='application/json'
    )


@app.route('/submissions/<submission_uuid>/spreadsheet', methods=['GET'])
def submission_spreadsheet(submission_uuid):
    try:
        spreadsheet = SpreadsheetStorageService(SPREADSHEET_STORAGE_DIR).retrieve(submission_uuid)
        spreadsheet_name = spreadsheet["name"]
        spreadsheet_blob = spreadsheet["blob"]

        return send_file(
            io.BytesIO(spreadsheet_blob),
            mimetype='application/octet-stream',
            as_attachment=True,
            attachment_filename=spreadsheet_name)
    except SubmissionSpreadsheetDoesntExist as e:
        return app.response_class(
            response={"message": f'No spreadsheet found for submission with uuid {submission_uuid}'},
            status=404,
            mimetype='application/json'
        )


@app.route('/projects/<project_uuid>/summary', methods=['GET'])
def project_summary(project_uuid):
    project = IngestApi().get_project_by_uuid(project_uuid)
    summary = SummaryService().summary_for_project(project)

    return app.response_class(
        response=jsonpickle.encode(summary, unpicklable=False),
        status=200,
        mimetype='application/json'
    )


def _submit_spreadsheet_data(importer, path, submission_url, project_uuid):

    logger.info("Attempting submission...")
    thread = threading.Thread(target=_do_import, args=(importer, path, submission_url, project_uuid))
    thread.start()
    logger.info("Spreadsheet upload started!")
    return submission_url


def _do_import(importer, path, submission_url, project_uuid):
    submission = importer.import_file(path, submission_url, project_uuid)
    importer.insert_uuids(submission, path)
    return


def _check_for_project(ingest_api):
    logger.info("Checking for project_id")
    project = None
    if 'project_id' in request.form:
        project_id = request.form['project_id']
        logger.info("Found project_id: " + project_id)

        project = ingest_api.get_project_by_id(project_id)

    else:
        logger.info("No existing project_id found")

    return project


def _save_spreadsheet(submission_uuid):
    logger.info("Saving file")
    try:
        path = _save_file(submission_uuid)
    except Exception as err:
        logger.error(traceback.format_exc())
        message = "We experienced a problem when saving your spreadsheet"
        raise SpreadsheetUploadError(500, message, str(err))
    return path


def _check_token():
    logger.info("Checking token")
    token = request.headers.get('Authorization')
    if token is None:
        raise SpreadsheetUploadError(401, "An authentication token must be supplied when uploading a spreadsheet",
                                     "")
    return token


def _save_file(submission_uuid):
    request_file = request.files['file']
    spreadsheet_storage_service = SpreadsheetStorageService(
            SPREADSHEET_STORAGE_DIR)
    path = spreadsheet_storage_service.store(submission_uuid, request_file.read())
    logger.info("Saved file to: " + path)
    return path


def create_upload_success_response(submission_url):
    ingest_api = IngestApi()
    submission_uuid = ingest_api.get_object_uuid(submission_url)
    display_id = submission_uuid or '<UUID not generated yet>'
    submission_id = submission_url.rsplit('/', 1)[-1]

    data = {
        "message": "We’ve got your spreadsheet, and we’re currently importing and validating the data. Nothing else for you to do - check back later.",
        "details": {
            "submission_url": submission_url,
            "submission_uuid": submission_uuid,
            "display_uuid": display_id,
            "submission_id": submission_id
        }
    }

    success_response = app.response_class(
        response=json.dumps(data),
        status=201,
        mimetype='application/json'
    )
    return success_response


def create_upload_failure_response(status_code, message, details):
    data = {
        "message": message,
        "details": details,
    }
    failure_response = app.response_class(
        response=json.dumps(data),
        status=status_code,
        mimetype='application/json'
    )
    print(failure_response)
    return failure_response
