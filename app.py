
import base64
import os
import shutil
import subprocess
import tempfile
import uuid
import zipfile
import cv2
from flask import Flask, request, make_response
from facedetect import ensure_dir, get_name_and_extension, main_for_file

ensure_dir('output')

app = Flask(__name__)


class DetectRouteKeys:
    numeric_keys = set(['maxfaces', 'minheight', 'minwidth', 'multiplier'])
    alpha_keys = set(['operation', 'mimetype', 'filename'])
    base64_keys = set(['imagedata'])
    all_keys: set[str]
    required_keys: set[str]


DetectRouteKeys.all_keys = DetectRouteKeys.numeric_keys.union(DetectRouteKeys.alpha_keys).union(DetectRouteKeys.base64_keys)
DetectRouteKeys.required_keys = DetectRouteKeys.all_keys


def process_image_data(image, name, ext, dirpath):
    with tempfile.NamedTemporaryFile('wb+') as img:
        img.write(image)
        pixels = cv2.imread(img.name)

    boxes = main_for_file(pixels)

    if boxes:
        ensure_dir(dirpath)
        for idx, box in enumerate(boxes):
            filepath = os.path.join(dirpath, '{}-face{}{}'.format(name, idx, ext))
            cv2.imwrite(filepath, box)
    else:
        return 'No faces detected', 404


def validate_body(body):
    if not all(i in DetectRouteKeys.required_keys for i in body.keys()):
        return 'Request body missing keys', 400

    for key in DetectRouteKeys.numeric_keys:
        try:
            body[key] = int(body[key])
        except (ValueError, TypeError) as e:
            return 'Expected data to be numeric', 400
        except Exception:
            return 'A problem occurred', 500

    return body, None


def zipped_response(zipfilename, zippingdir):
    shutil.make_archive(zipfilename, 'zip', zippingdir)
    with open(zipfilename + '.zip', 'rb') as result:
        resp = make_response(result.read())
        resp.headers['Content-Type'] = 'application/zip'
        return resp


@app.post('/detectall')
def detectall():
    body = request.json

    body, error = validate_body(body)
    if error is not None:
        return body, error

    job_id = str(uuid.uuid4())

    dirpath = os.path.join('.', 'output', job_id)
    archive = os.path.join('.', 'output', job_id + '-archive')
    ensure_dir(dirpath)
    try:
        zip = base64.urlsafe_b64decode(body['imagedata'])
        name, ext = get_name_and_extension(body['filename'])

        assert '..' not in ext and all(i == '.' or i.isalnum() for i in ext)
        with tempfile.NamedTemporaryFile('wb+') as img:
            img.write(zip)

            with tempfile.TemporaryDirectory() as directory:
                source_archive = zipfile.ZipFile(img.name)
                names = source_archive.filelist
                for name in names:
                    source_archive.extract(name, directory)

                for image in os.listdir(directory):
                    name, ext = get_name_and_extension(image)
                    fullpath = os.path.join(directory, image)
                    if not os.path.isdir(fullpath):
                        with open(fullpath, 'rb') as i:
                            process_image_data(i.read(), name, ext, dirpath)

        resp = zipped_response(archive, dirpath)
        shutil.rmtree(dirpath)
        os.unlink(archive + '.zip')
        return resp

    except Exception as e:
        shutil.rmtree(dirpath)
        if os.path.exists(archive + '.zip'):
            os.unlink(archive + '.zip')
        return 'Could not process request', 499


@app.post('/detect')
def detect():
    body = request.json

    body, error = validate_body(body)
    if error is not None:
        return body, error

    try:
        image = base64.urlsafe_b64decode(body['imagedata'])
        name, ext = get_name_and_extension(body['filename'])

        assert '..' not in ext and all(i == '.' or i.isalnum() for i in ext)

        job_id = str(uuid.uuid4())
        dirpath = os.path.join('.', 'output', job_id)
        archive = os.path.join('.', 'output', job_id + '-archive')
        process_image_data(image, name, ext, dirpath)

        resp = zipped_response(archive, dirpath)
        shutil.rmtree(dirpath)
        os.unlink(archive + '.zip')
        return resp

    except Exception as e:
        if os.path.isdir(dirpath):
            shutil.rmtree(dirpath)
        if os.path.exists(archive + '.zip'):
            os.unlink(archive + '.zip')
        return 'Could not process request', 499


@app.get('/')
def index():
    with open("static/index.html") as f:
        return f.read()


if __name__ == '__main__':
    from waitress import serve
    serve(app, host='0.0.0.0', port=8000)
