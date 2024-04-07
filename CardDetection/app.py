from chalice import Chalice
from chalicelib import storage_service
from chalicelib import recognition_service
from chalicelib import translation_service
from chalicelib import speech_service
from chalicelib import comprehend_service

import base64
import json
import os

app = Chalice(app_name='CardDetection')
app.debug = True

#####
# services initialization
#####
storage_location = 'contentcen301278498.aws.ai'
storage_service = storage_service.StorageService(storage_location)
recognition_service = recognition_service.RecognitionService(storage_service)
translation_service = translation_service.TranslationService()



@app.route('/')
def index():
    return {'hello': 'world'}


# The view function above will return {"hello": "world"}
# whenever you make an HTTP GET request to '/'.
#
# Here are a few more examples:
#
# @app.route('/hello/{name}')
# def hello_name(name):
#    # '/hello/james' -> {"hello": "james"}
#    return {'hello': name}
#
# @app.route('/users', methods=['POST'])
# def create_user():
#     # This is the JSON body the user sent in their POST request.
#     user_as_json = app.current_request.json_body
#     # We'll echo the json body back to the user in a 'user' key.
#     return {'user': user_as_json}
#
# See the README documentation for more examples.
#

@app.route('/login', methods=['POST'])
def login():
    



    return {}


#####
# RESTful endpoints
#####
@app.route('/images', methods = ['POST'], cors = True)
def upload_image():
    """processes file upload and saves file to storage service"""
    request_data = json.loads(app.current_request.raw_body)
    file_name = request_data['filename']
    file_bytes = base64.b64decode(request_data['filebytes'])

    image_info = storage_service.upload_file(file_bytes, file_name)

    return image_info


@app.route('/images/{image_id}/translate-text', methods = ['POST'], cors = True)
def translate_image_text(image_id):
    """detects then translates text in the specified image"""
    request_data = json.loads(app.current_request.raw_body)
    from_lang = request_data['fromLang']
    to_lang = request_data['toLang']

    MIN_CONFIDENCE = 80.0

    text_lines = recognition_service.detect_text(image_id)

    translated_lines = []
    for line in text_lines:
        # check confidence
        if float(line['confidence']) >= MIN_CONFIDENCE:
            translated_line = translation_service.translate_text(line['text'], from_lang, to_lang)
            translated_lines.append({
                'text': line['text'],
                'translation': translated_line,
                'boundingBox': line['boundingBox']
            })

    return translated_lines


# this function will pass the transalted text to speech_service.py file and receivce the JSON data.
@app.route('/images/translate-text/speech', methods = ['POST'], cors = True)
def generate_speech():
    request_data = json.loads(app.current_request.raw_body)
    text = request_data['text']
    response = speech_service.convert_to_speech(text)
    return response


@app.route('/images/{image_id}/analyze-entities', methods=['POST'], cors=True)
def analyze_entities(image_id):
    """Detects entities in the text of the specified image"""
    request_data = json.loads(app.current_request.raw_body)
    text = request_data['text']

    # Analyze entities using Comprehend
    entities = comprehend_service.detect_entities(text)
    return {'entities': entities}