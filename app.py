
import base64
import binascii
import os
import shutil
import sys
import tempfile
import threading
import uuid
import webbrowser
import zipfile
from multiprocessing import Pool
from typing import Any, Optional, Tuple, Union

import cv2
from flask import Flask, Response, make_response, request

from appclasses import *
from facedetect import ensure_dir, get_name_and_extension, main_for_file
from shrink import resize_image_bytes

ensure_dir('output')

app = Flask(__name__)


def next_job_id():
    return str(uuid.uuid4())


def process_image_data(image: bytes, name: str, ext: str, dirpath: str, options: FaceDetectOptions) -> Union[Tuple[None, None], Tuple[str, int]]:
    with tempfile.NamedTemporaryFile('wb+') as img:
        img.write(image)
        pixels = cv2.imread(img.name)

    ensure_dir(dirpath)

    if pixels is None:
        return 'No faces detected', 498

    boxes = main_for_file(pixels, options.drawOnly, options.limit, options.squeeze, options.pad, options.resize, options.multiplier, options.minw, options.minh)
    if len(boxes) > 0:
        for idx, box in enumerate(boxes):
            filepath = os.path.join(dirpath, '{}-face{}{}'.format(name, idx, ext))
            cv2.imwrite(filepath, box)
        return None, None
    else:
        return 'No faces detected', 404


def validate_body(body: Any, KeySetClass) -> Tuple[Union[str, Any], Optional[int]]:
    if not all(i in KeySetClass.required_keys for i in body.keys()):
        return 'Request body missing keys', 400

    for key in KeySetClass.numeric_keys:
        try:
            body[key] = int(body[key])
        except (ValueError, TypeError) as e:
            return 'Expected data to be numeric', 400
        except Exception:
            return 'A problem occurred', 500

    return body, None


def zipped_response(zipfilename: str, zippingdir: str) -> Response:
    shutil.make_archive(zipfilename, 'zip', zippingdir)
    with open(zipfilename + '.zip', 'rb') as result:
        resp = make_response(result.read())
        resp.headers['Content-Type'] = 'application/zip'
        return resp


def do_multiprocess(path: str, name: str, ext: str, dirpath: str, options: FaceDetectOptions):
    with open(path, 'rb') as i:
        process_image_data(i.read(), name, ext, dirpath, options)


@app.post('/detectall')
def detectall():
    body = request.json

    body, error = validate_body(body, DetectRouteKeys)
    if error is not None:
        return body, error

    options = FaceDetectOptions.frombody(body)

    job_id = next_job_id()

    dirpath = os.path.join('.', 'output', job_id)
    archive = os.path.join('.', 'output', job_id + '-archive')
    ensure_dir(dirpath)
    try:
        try:
            zip = base64.urlsafe_b64decode(body['imagedata'])
        except binascii.Error as e:
            raise ValueError from e

        _, ext = get_name_and_extension(body['filename'])

        assert '..' not in ext and all(i == '.' or i.isalnum() for i in ext)
        with tempfile.NamedTemporaryFile('wb+') as img:
            img.write(zip)

            with tempfile.TemporaryDirectory() as directory:
                source_archive = zipfile.ZipFile(img.name)
                names = source_archive.filelist
                for name in names:
                    source_archive.extract(name, directory)

                collection = []
                for image in os.listdir(directory):
                    name, ext = get_name_and_extension(image)
                    if '..' in name or '/' in name or '..' in ext or '/' in ext:
                        raise FileNameError()
                    fullpath = os.path.join(directory, image)
                    if not os.path.isdir(fullpath):
                        collection.append((fullpath, name, ext, dirpath, options))

                with Pool() as pool:
                    for result in pool.starmap(do_multiprocess, collection):
                        print('completed {}'.format(result))

        resp = zipped_response(archive, dirpath)
        return resp
    except FileNameError as e:
        if os.environ["DEBUG"]:
            raise e
        return 'A file in your zip archive has an invalid name', 400
    except ValueError as e:
        if os.environ["DEBUG"]:
            raise e
        return 'Invalid zip file', 400
    except Exception as e:
        if os.environ["DEBUG"]:
            raise e
        return 'Could not process request', 499
    finally:
        if os.path.isdir(dirpath):
            shutil.rmtree(dirpath)
        if os.path.exists(archive + '.zip'):
            os.unlink(archive + '.zip')


@app.post('/detect')
def detect():
    body = request.json

    body, error = validate_body(body, DetectRouteKeys)
    if error is not None:
        return body, error

    options = FaceDetectOptions.frombody(body)

    try:
        try:
            image = base64.urlsafe_b64decode(body['imagedata'])
        except binascii.Error as e:
            raise ValueError from e

        name, ext = get_name_and_extension(body['filename'])

        assert '..' not in ext and all(i == '.' or i.isalnum() for i in ext)
        if '..' in name or '/' in name or '..' in ext or '/' in ext:
            raise FileNameError()

        job_id = str(uuid.uuid4())
        dirpath = os.path.join('.', 'output', job_id)
        archive = os.path.join('.', 'output', job_id + '-archive')

        msg, code = process_image_data(image, name, ext, dirpath, options)

        if msg is not None:
            resp = msg, code
        else:
            resp = zipped_response(archive, dirpath)
            os.unlink(archive + '.zip')

        shutil.rmtree(dirpath)
        return resp
    except FileNameError:
        return 'Invalid file name', 400
    except ValueError as e:
        return 'Invalid image file', 400
    except Exception as e:
        return 'Could not process request', 499
    finally:
        if os.path.isdir(dirpath):
            shutil.rmtree(dirpath)
        if os.path.exists(archive + '.zip'):
            os.unlink(archive + '.zip')


@app.post('/do-shrink')
def do_shrink():

    body = request.json

    body, error = validate_body(body, ShrinkRouteKeys)
    if error is not None:
        print(body, error)
        return body, error

    options = ShrinkOptions.frombody(body)

    try:
        try:
            image = base64.urlsafe_b64decode(body['imagedata'])
        except binascii.Error as e:
            raise ValueError from e

        name, ext = get_name_and_extension(body['filename'])

        assert '..' not in ext and all(i == '.' or i.isalnum() for i in ext)
        if '..' in name or '/' in name or '..' in ext or '/' in ext:
            raise FileNameError()

        job_id = str(uuid.uuid4())
        dirpath = os.path.join('.', 'output', job_id)
        archive = os.path.join('.', 'output', job_id + '-archive')
        ensure_dir(dirpath)

        result = resize_image_bytes(image, options.newwidth, options.newheight)

        if result is None:
            resp = 'Could not shrink image', 500
        else:
            cv2.imwrite(os.path.join(dirpath, '{}-shrunk{}'.format(name, ext)), result)
            resp = zipped_response(archive, dirpath)

        return resp
    except FileNameError:
        return 'Invalid file name', 400
    except InvalidImageSizeError:
        return 'The Image Size cannot be 0x0', 400
    except ValueError as e:
        return 'Invalid image file', 400
    except Exception as e:
        return 'Could not process request', 499
    finally:
        if os.path.isdir(dirpath):
            shutil.rmtree(dirpath)
        if os.path.exists(archive + '.zip'):
            os.unlink(archive + '.zip')


@app.get('/')
def index():
    with open("static/index.html") as f:
        return f.read()


@app.get('/shrink')
def shrink():
    with open('static/shrink.html') as f:
        return f.read()


if __name__ == '__main__':
    from waitress import serve

    t = threading.Thread(target=lambda: serve(app, host='0.0.0.0', port=8000))
    t.start()
    if 'DEBUG' not in os.environ:
        if 'darwin' in sys.platform:
            webbrowser.MacOSXOSAScript('Safari').open('localhost:8000', 2)
        else:
            webbrowser.open_new_tab('localhost:8000')
    t.join()
