import base64
import boto3
import json
import os
import posixpath
import uuid
from flask import Flask, jsonify, render_template, request, redirect, url_for

app = Flask(__name__)


def generate_random_id():
    return base64.urlsafe_b64encode(uuid.uuid4().bytes).decode('utf8').rstrip('=')


def mustachify(original_image_url):
    # Do the mustache dance

    # Put the result on S3
    result_id = generate_random_id()

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
    result_id = mustachify(avatar_url)

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
