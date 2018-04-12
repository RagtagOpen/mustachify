import base64
import errno
import hashlib
import io
import json
import math
import os
import posixpath
import random
import shutil
import urllib.parse
import uuid

import boto3
from flask import Flask, flash, redirect, render_template, request, url_for
from PIL import Image


def generate_random_id():
    return base64.urlsafe_b64encode(uuid.uuid4().bytes).decode('utf8').rstrip('=')


app = Flask(__name__)
app.config['SECRET_KEY'] = generate_random_id()
app.config['ALLOWED_EXTENSIONS'] = set(['png', 'jpg', 'jpeg'])


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower(
           ) in app.config.get('ALLOWED_EXTENSIONS')


def watermark(im, position=(100, 100)):
    mark = Image.open('watermark.jpg')
    if im.mode != 'RGBA':
        im = im.convert('RGBA')

    # create a transparent layer the size of the image and draw the
    # watermark in that layer.
    layer = Image.new('RGBA', im.size, (0, 0, 0, 0))

    # scale the watermark to the size of the image
    ratio = min(
        float(im.size[0]) / mark.size[0], float(im.size[1]) / mark.size[1])
    w = int(mark.size[0] * ratio * 0.3)
    h = int(mark.size[1] * ratio * 0.3)
    mark = mark.resize((w, h), Image.ANTIALIAS)
    layer.paste(mark, (im.size[0] - w - 10, im.size[1] - h - 10))

    # composite the watermark with the layer
    return Image.composite(layer, im, layer)


def remove_transparency(im, bg_color=(255, 255, 255)):

    # Only process if image has transparency (http://stackoverflow.com/a/1963146)
    if im.mode == 'P' and 'transparency' in im.info:
        im = im.convert('RGBA')

    if im.mode in ('RGBA', 'LA'):
        bg = Image.new('RGBA', im.size, (255, 255, 255, 255))
        im = im.convert('RGBA')
        composite = Image.alpha_composite(bg, im).convert('RGB')

        return composite
    else:
        return im


class NoFacesFoundException(Exception):
    pass

# image rotation code from https://github.com/kylefox/python-image-orientation-patch/


# The EXIF tag that holds orientation data.
EXIF_ORIENTATION_TAG = 274

# Obviously the only ones to process are 3, 6 and 8.
# All are documented here for thoroughness.
ORIENTATIONS = {
    1: ("Normal", 0),
    2: ("Mirrored left-to-right", 0),
    3: ("Rotated 180 degrees", Image.ROTATE_180),
    4: ("Mirrored top-to-bottom", 0),
    5: ("Mirrored along top-left diagonal", 0),
    6: ("Rotated 90 degrees", Image.ROTATE_270),
    7: ("Mirrored along top-right diagonal", 0),
    8: ("Rotated 270 degrees", Image.ROTATE_90)
}


def remove_exif_rotation(img):
    try:
        orientation = img._getexif()[EXIF_ORIENTATION_TAG]
    except (TypeError, AttributeError, KeyError):
        return img

    if orientation in [3, 6, 8]:
        degrees = ORIENTATIONS[orientation][1]
        img = img.transpose(degrees)

    return img


def limit_image_size(img):
    # Limit to 1000x1000 pixels, but maintain the existing aspect ratio
    img.thumbnail((1000, 1000))

    return img


def apply_mustache(s3_bucket, image_data):
    # Load the image into memory
    image_data.stream.seek(0)
    original_buf = io.BytesIO(image_data.read())
    original_buf.seek(0)

    original_img = Image.open(original_buf)

    rotated_image_img = remove_exif_rotation(original_img)
    del original_img

    reduced_image_img = limit_image_size(rotated_image_img)
    del rotated_image_img

    reduced_image_img = remove_transparency(reduced_image_img)

    reduced_image_buf = io.BytesIO()
    reduced_image_img.save(reduced_image_buf, 'JPEG', quality=80)
    reduced_image_buf.seek(0)
    del reduced_image_img

    mustachioed_buf = mustachify(reduced_image_buf)

    # Put that image on S3
    # since we're just working with the buffer, the uploaded image happily won't have any EXIF data.
    s3 = boto3.client("s3", 'us-east-1')
    result_id = generate_random_id()
    result_key = posixpath.join('result', result_id) + ".jpg"
    s3.upload_fileobj(
        mustachioed_buf, s3_bucket, result_key,
        ExtraArgs={
            'ContentType': 'image/jpeg',
            'ACL': 'public-read',
        }
    )

    # Return an ID for the mustachioed image
    return result_id


def rekognize(original_image_buf):
    cache_key = base64.urlsafe_b64encode(
        hashlib.sha1(original_image_buf.getvalue()).digest()
    ).decode('utf8').rstrip('=')

    cache_dir = os.path.join(os.getcwd(), 'cache')
    if not os.path.exists(cache_dir):
        os.mkdir(cache_dir)

    cache_path = os.path.join(cache_dir, cache_key)

    try:
        with open(cache_path, 'r') as f:
            print("Returning cached Rekognition data")
            return json.load(f)
    except IOError as e:
        if e.errno == errno.ENOENT:
            pass

    # Send it to Rekognition
    rekognition = boto3.client("rekognition", 'us-east-1')
    response = rekognition.detect_faces(
        Image={
            'Bytes': original_image_buf.getvalue()
        }
    )

    with open(cache_path, 'w') as f:
        print("Storing Rekognition data")
        json.dump(response, f)

    return response


def scale_rotate_translate(image, angle, center=None, new_center=None, scale=None):
    if center is None:
        return image.rotate(angle)

    angle = -angle / 180.0 * math.pi
    nx, ny = x, y = center
    sx = sy = 1.0

    if new_center:
        (nx, ny) = new_center

    if scale:
        (sx, sy) = scale

    cosine = math.cos(angle)
    sine = math.sin(angle)
    a = cosine / sx
    b = sine / sx
    c = x - nx * a - ny * b
    d = -sine / sy
    e = cosine / sy
    f = y - nx * d - ny * e

    return image.transform(
        image.size,
        Image.AFFINE,
        (a, b, c, d, e, f),
        resample=Image.BICUBIC,
        fillcolor='red',
    )


MUSTACHES = {
    'mustache.png': {
        'center': (526, 385),
        'mouth_starts_at': 0,
        'mustache_width_ratio': 1.25,
    }
}


def mustachify(original_image_buf):
    response = rekognize(original_image_buf)

    if not response['FaceDetails']:
        raise NoFacesFoundException()

    im = Image.open(original_image_buf)
    im = remove_transparency(im)
    at_least_one_face = False
    for face in response['FaceDetails']:
        if face['Confidence'] < 0.9:
            # Only work on things we're really sure are faces
            app.logger.info(
                "Skipping face with confidence < 0.9: %s", face['Confidence'])
            continue

        if abs(face['Pose']['Yaw']) > 35:
            # Only work on faces that are looking at the camera
            app.logger.info(
                "Skipping face with yaw greater than 35: %s", face['Pose']['Yaw'])
            continue

        at_least_one_face = True

        landmarks = dict([
            (l['Type'], (l['X'] * im.size[0], l['Y'] * im.size[1]))
            for l in face.get('Landmarks')
        ])

        mleft_x, mleft_y = landmarks['mouthLeft']
        mright_x, mright_y = landmarks['mouthRight']
        mcenter_x, mcenter_y = (
            (mleft_x + mright_x) / 2,
            (mleft_y + mright_y) / 2,
        )

        nose_x, nose_y = landmarks['nose']
        desired_upper_lip_height = math.sqrt(
            (nose_x - mcenter_x) ** 2 +
            (nose_y - mcenter_y) ** 2
        )
        desired_mouth_width = math.sqrt(
            (mright_x - mleft_x) ** 2 +
            (mright_y - mleft_y) ** 2
        )

        mustache_image_name, mustache_params = random.choice(
            list(MUSTACHES.items()))

        # If the mustache is smaller than the original image, make an image to
        # move the mustache around in because affine transform doesn't
        # expand for you
        mustache_im = Image.open(mustache_image_name)
        if mustache_im.size[0] < im.size[0] and mustache_im.size[1] < im.size[1]:
            mustache_overlay = Image.new('RGBA', im.size)
            # Put the mustache image in the overlay
            mustache_overlay.paste(mustache_im, mustache_im)
        else:
            # But if the mustache image is already bigger than the image
            # we'll have room to do the scale/rotate/translate, so no need
            # to create the overaly.
            mustache_overlay = mustache_im

        mustache_upper_lip_height = (
            mustache_im.size[1] - mustache_params['mouth_starts_at'])

        height_scale = desired_upper_lip_height / mustache_upper_lip_height
        width_scale = (desired_mouth_width *
                       mustache_params['mustache_width_ratio']) / mustache_im.size[0]

        alpha = math.degrees(
            math.atan2(
                (mright_y - mleft_y),
                (mright_x - mleft_x)
            )
        )
        rotation = alpha * -1.0

        mustache_overlay = scale_rotate_translate(
            mustache_overlay,
            rotation,
            mustache_params['center'],
            (mcenter_x, mcenter_y),
            (width_scale, height_scale),
        )

        im.paste(mustache_overlay, (0, 0), mustache_overlay)

    if not at_least_one_face:
        raise NoFacesFoundException()

    # Save the result as a JPEG in memory
    buf = io.BytesIO()
    im = watermark(im)
    im = remove_transparency(im)
    im.save(buf, 'JPEG', quality=80)
    buf.seek(0)

    return buf


@app.route('/')
def index():
    return render_template(
        'home.html',
        origin=request.args.get('origin') or '',
    )


@app.route('/result/new', methods=["POST"])
def submit_form():
    file = request.files.get("original")
    origin = request.form.get('origin') or ''

    if not file or file.filename == '':
        flash("Oops, you didn't select a file. Please try again!")
        return redirect(url_for('index', origin=origin))

    if not allowed_file(file.filename):
        flash("We can't add a mustache to that kind of file. Try a file ending in .png, .jpg or .jpeg")
        return redirect(url_for('index', origin=origin))

    # Mustachify the image
    try:
        result_id = apply_mustache(os.environ.get('S3_BUCKET'), file)
    except NoFacesFoundException:
        flash("Oh no! I couldn't find any faces on your picture. Please try again with a clearer picture.")
        return redirect(url_for('index', origin=origin))

    # And show them the mustachioed image
    return redirect(url_for('show_result', result_id=result_id, origin=origin))


@app.route('/result/<result_id>')
def show_result(result_id):
    return render_template(
        'show.html',
        # First iteration involves just sharing homepage via FB. More sophisticated sharing may come down the pike later.
        shareable_url=os.environ.get('ROOT_URL'),
        mustachioed_url=posixpath.join(
            'https://s3.amazonaws.com/',
            os.environ.get('S3_BUCKET'),
            'result',
            result_id + ".jpg"
        ),
    )


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('infile', type=argparse.FileType('rb'))
    parser.add_argument('outfile', type=argparse.FileType('wb'))
    args = parser.parse_args()

    input_buf = io.BytesIO()
    shutil.copyfileobj(args.infile, input_buf)
    output_buf = mustachify(input_buf)
    shutil.copyfileobj(output_buf, args.outfile)

    # port = int(os.environ.get('PORT', 5000))
    # app.run(host='0.0.0.0', port=port)
