import base64
import boto3
import errno
import hashlib
import io
import json
import math
import os
import posixpath
import random
import shutil
import uuid
from flask import Flask, flash, render_template, request, redirect, url_for
from PIL import Image


def generate_random_id():
    return base64.urlsafe_b64encode(uuid.uuid4().bytes).decode('utf8').rstrip('=')


app = Flask(__name__)
app.config['SECRET_KEY'] = generate_random_id()
app.config['ALLOWED_EXTENSIONS'] = set(['png', 'jpg', 'jpeg', 'gif'])


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config.get('ALLOWED_EXTENSIONS')


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


def apply_mustache(s3_bucket, image_data):
    # Load the image into memory
    image_data.stream.seek(0)
    original_buf = io.BytesIO(image_data.read())
    original_buf.seek(0)

    mustachioed_buf = mustachify(original_buf)

    # Put that image on S3
    s3 = boto3.client("s3", 'us-east-1')
    result_id = generate_random_id()
    result_key = posixpath.join('result', result_id)
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

    try:
        with open(cache_key, 'r') as f:
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

    with open(cache_key, 'w') as f:
        print("Storing Rekognition data")
        json.dump(response, f)

    return response


def scale_rotate_translate(image, angle, center=None, new_center=None, scale=None):
    if center is None:
        return image.rotate(angle)

    angle = -angle/180.0*math.pi
    nx, ny = x, y = center
    sx = sy = 1.0

    if new_center:
        (nx, ny) = new_center

    if scale:
        (sx, sy) = scale

    cosine = math.cos(angle)
    sine = math.sin(angle)
    a = cosine/sx
    b = sine/sx
    c = x-nx*a-ny*b
    d = -sine/sy
    e = cosine/sy
    f = y-nx*d-ny*e

    return image.transform(
        image.size,
        Image.AFFINE,
        (a, b, c, d, e, f),
        resample=Image.BICUBIC,
        fillcolor='red',
    )


MUSTACHES = {
    'mustache_test.png': {
        'center': (1039, 802),
        'mouth_starts_at': 18
    }
}


def mustachify(original_image_buf):
    response = rekognize(original_image_buf)

    if not response['FaceDetails']:
        raise NoFacesFoundException()

    im = Image.open(original_image_buf)
    for face in response['FaceDetails']:
        if face['Confidence'] < 0.9:
            # Only work on things we're really sure are faces
            continue

        if abs(face['Pose']['Yaw']) > 30:
            # Only work on faces that are looking at the camera
            continue

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

        mustache_image_name, mustache_params = random.choice(list(MUSTACHES.items()))

        # If the mustache is smaller than the original image, make an image to
        # move the mustache around in because affine transform doesn't
        # expand for you
        mustache_im = Image.open(mustache_image_name)
        if mustache_im.size[0] < im.size[0] or mustache_im.size[1] < im.size[1]:
            mustache_overlay = Image.new('RGBA', im.size)
            # Put the mustache image in the overlay
            mustache_overlay.paste(mustache_im, mustache_im)
        else:
            # But if the mustache image is already bigger than the image
            # we'll have room to do the scale/rotate/translate, so no need
            # to create the overaly.
            mustache_overlay = mustache_im

        mustache_upper_lip_height = (mustache_im.size[1] - mustache_params['mouth_starts_at'])

        height_scale = desired_upper_lip_height / mustache_upper_lip_height
        width_scale = desired_mouth_width / mustache_im.size[0]

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

    # Save the result as a JPEG in memory
    buf = io.BytesIO()
    im = remove_transparency(im)
    im.save(buf, 'JPEG', quality=80)
    buf.seek(0)

    return buf


@app.route('/')
def index():
    return render_template(
        'home.html',
    )


@app.route('/result/new', methods=["POST"])
def submit_form():
    file = request.files.get("original")

    if not file or file.filename == '':
        flash("Oops, you didn't select a file. Please try again!")
        return redirect(url_for('index'))

    if allowed_file(file):
        flash("We can't add a mustache to that kind of file. Try a file ending in .png, .jpg, or .gif.")
        return redirect(url_for('index'))

    # Mustachify the image
    try:
        result_id = apply_mustache(os.environ.get('S3_BUCKET'), file)
    except NoFacesFoundException:
        flash("Oh no! I couldn't find any faces on your picture. Please try again with a clearer picture.")
        return redirect(url_for('index'))

    # And show them the mustachioed image
    return redirect(url_for('show_result', result_id=result_id))


@app.route('/result/<result_id>')
def show_result(result_id):
    return render_template(
        'show.html',
        mustachioed_url=posixpath.join(
            'https://s3.amazonaws.com/',
            os.environ.get('S3_BUCKET'),
            'result',
            result_id
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
