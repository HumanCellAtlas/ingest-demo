#!/usr/bin/env python

import io
import logging
import os
import sys
import threading
import traceback

import jsonpickle
from flask import Flask, request, redirect, send_file
from flask import json
from flask_cors import CORS, cross_origin
from ingest.api.ingestapi import IngestApi
from ingest.importer.importer import XlsImporter
from ingest.importer.spreadsheetUploadError import SpreadsheetUploadError

from broker.service.spreadsheet_storage.spreadsheet_storage_exceptions import SubmissionSpreadsheetDoesntExist
from broker.service.spreadsheet_storage.spreadsheet_storage_service import SpreadsheetStorageService
from broker.service.spreadsheet_upload_service import SpreadsheetUploadService
from broker.service.summary_service import SummaryService

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

SPREADSHEET_UPLOAD_MESSAGE = "We’ve got your spreadsheet, and we’re currently importing and validating the data.\
Nothing else for you to do - check back later."

SPREADSHEET_UPLOAD_MESSAGE_ERROR = "We experienced a problem while uploading your spreadsheet"

ingest_api = IngestApi()
storage_service = SpreadsheetStorageService(SPREADSHEET_STORAGE_DIR)
importer = XlsImporter(ingest_api)
spreadsheet_upload_service = SpreadsheetUploadService(ingest_api, storage_service, importer)


@app.route('/', methods=['GET'])
def index():
    new_ui_url = os.environ.get('INGEST_UI')
    if new_ui_url:
        return redirect(new_ui_url, code=302)
    return app.response_class(
        response=json.dumps({'message': "Ingest Broker API is running!"}),
        status=200,
        mimetype='application/json'
    )


@app.route('/api_upload', methods=['POST'])
@cross_origin()
def upload_spreadsheet():
    return _upload_spreadsheet()


@app.route('/api_upload_update', methods=['POST'])
@cross_origin()
def upload_update_spreadsheet():
    _set_token()
    return _upload_spreadsheet(is_update=True)


@app.route('/submissions/<submission_uuid>/spreadsheet', methods=['GET'])
def get_submission_spreadsheet(submission_uuid):
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


@app.route('/submissions/<submission_uuid>/summary', methods=['GET'])
def submission_summary(submission_uuid):
    submission = IngestApi().get_submission_by_uuid(submission_uuid)
    summary = SummaryService().summary_for_submission(submission)

    return app.response_class(
        response=jsonpickle.encode(summary, unpicklable=False),
        status=200,
        mimetype='application/json'
    )


def _upload_spreadsheet(is_update=False):
    try:
        _set_token()
        logger.info('Uploading spreadsheet!')
        submission_resource = _async_upload(request, is_update)

    except SpreadsheetUploadError as spreadsheetUploadError:
        return _failure_response(spreadsheetUploadError.http_code,
                                 spreadsheetUploadError.message,
                                 spreadsheetUploadError.details)
    except Exception as err:
        logger.error(traceback.format_exc())
        return _failure_response(500, SPREADSHEET_UPLOAD_MESSAGE_ERROR, str(err))

    else:
        return _success_response(submission_resource)


def _async_upload(request, is_update):
    submission_resource = ingest_api.create_submission(update_submission=is_update)
    logger.info(f'Created Submission: {submission_resource["_links"]["self"]["href"]}')

    thread = threading.Thread(target=spreadsheet_upload_service.upload,
                              args=(submission_resource, request.files['file'], request.form.get('projectUuid')))
    thread.start()
    return submission_resource


def _set_token():
    logger.info("Checking token")
    token = request.headers.get('Authorization')
    ingest_api.set_token(token)
    if token is None:
        raise SpreadsheetUploadError(401, "An authentication token must be supplied when uploading a spreadsheet", "")
    return token


def _success_response(submission_resource):
    submission_uuid = submission_resource['uuid']['uuid']
    submission_url = submission_resource['_links']['self']['href']
    submission_id = submission_url.rsplit('/', 1)[-1]

    data = {
        'message': SPREADSHEET_UPLOAD_MESSAGE,
        'details': {
            'submission_url': submission_url,
            'submission_uuid': submission_uuid,
            'submission_id': submission_id
        }
    }

    success_response = app.response_class(
        response=json.dumps(data),
        status=201,
        mimetype='application/json'
    )
    return success_response


def _failure_response(status_code, message, details):
    data = {
        "message": message,
        "details": details,
    }
    failure_response = app.response_class(
        response=json.dumps(data),
        status=status_code,
        mimetype='application/json'
    )
    return failure_response


if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)

    app.run(host='0.0.0.0', port=5000)
