import base64
import boto3
import io
import json
import os
import posixpath
import requests
import uuid
from flask import Flask, flash, jsonify, render_template, request, redirect, url_for
from PIL import Image, ImageDraw


def generate_random_id():
    return base64.urlsafe_b64encode(uuid.uuid4().bytes).decode('utf8').rstrip('=')

app = Flask(__name__)
app.config['SECRET_KEY'] = generate_random_id()


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


def apply_mustache(s3_bucket, original_image_url):
    # Load the image into memory
    buf = io.BytesIO(requests.get(original_image_url).content)

    # Send it to Rekognition
    rekognition = boto3.client("rekognition", 'us-east-1')
    response = rekognition.detect_faces(
        Image={
            'Bytes': buf.getvalue()
        }
    )

    if not response['FaceDetails']:
        raise NoFacesFoundException()

    im = Image.open(buf)
    for face in response['FaceDetails']:
        if face['Confidence'] < 0.9:
            # Only work on things we're really sure are faces
            continue

        landmarks = dict([
            (l['Type'], (int(l['X'] * im.size[0]), int(l['Y'] * im.size[1])))
            for l in face.get('Landmarks')
        ])

        mustache_im = Image.open('mustache_test.png')

        nose_x, nose_y = landmarks['nose']
        mleft_x, mleft_y = landmarks['mouthLeft']
        mright_x, mright_y = landmarks['mouthRight']
        new_mustache_size = (mright_x - mleft_x, mleft_y - nose_y)

        mustache_im = mustache_im.resize(new_mustache_size)
        im.paste(mustache_im, (mleft_x, mleft_y - new_mustache_size[1]), mustache_im)

    # Save the result as a JPEG in memory
    buf = io.BytesIO()
    im = remove_transparency(im)
    im.save(buf, 'JPEG', quality=80)
    buf.seek(0)

    # Put that image on S3
    s3 = boto3.client("s3", 'us-east-1')
    result_id = generate_random_id()
    result_key = posixpath.join('result', result_id)
    s3.upload_fileobj(
        buf, s3_bucket, result_key,
        ExtraArgs={
            'ContentType': 'image/jpeg',
            'ACL': 'public-read',
        }
    )

    # Return an ID for the mustachioed image
    return result_id


@app.route('/')
def index():
    return render_template(
        'home.html',
        mustachioed_url="/static/media/default.png",
    )


@app.route('/result/new', methods=["POST"])
def submit_form():

    # Collect the data posted from the HTML form
    avatar_url = request.form["avatar-url"]

    # Mustachify the image
    try:
        result_id = apply_mustache(os.environ.get('S3_BUCKET'), avatar_url)
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


@app.route('/sign-s3')
def sign_s3():
    s3_bucket = os.environ.get('S3_BUCKET')
    file_type = request.args.get('file-type')
    result_id = generate_random_id()
    original_key = posixpath.join('original', result_id)

    s3 = boto3.client('s3')

    presigned_post = s3.generate_presigned_post(
        Bucket=s3_bucket,
        Key=original_key,
        Fields={
            "acl": "public-read",
            "Content-Type": file_type
        },
        Conditions=[
            {"acl": "public-read"},
            {"key": original_key},
            {"Content-Type": file_type},
            ["content-length-range", 1024, 5242880], # 1KB to 5MB
        ],
        ExpiresIn=1200
    )

    return jsonify({
        'data': presigned_post,
        'url': posixpath.join('https://s3.amazonaws.com/', s3_bucket, original_key),
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
