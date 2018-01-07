import base64
import boto3
import json
import os
import posixpath
import uuid
from flask import Flask, jsonify, render_template, request, redirect, url_for

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('home.html')


@app.route("/submit-form/", methods=["POST"])
def submit_form():

    # Collect the data posted from the HTML form
    avatar_url = request.form["avatar-url"]

    # TODO: Send this over to Rekognition API

    # For now, we'll just load homepage again.
    return render_template('home.html'), 201


@app.route('/sign-s3/')
def sign_s3():
    s3_bucket = os.environ.get('S3_BUCKET')
    file_type = request.args.get('file-type')
    file_name = posixpath.join('raw', base64.urlsafe_b64encode(uuid.uuid4().bytes).decode('utf8'))

    s3 = boto3.client('s3')

    presigned_post = s3.generate_presigned_post(
        Bucket=s3_bucket,
        Key=file_name,
        Fields={
            "acl": "public-read",
            "Content-Type": file_type
        },
        Conditions=[
            {"acl": "public-read"},
            {"key": file_name},
            {"Content-Type": file_type},
            ["content-length-range", 1024, 5242880], # 1KB to 5MB
        ],
        ExpiresIn=1200
    )

    return jsonify({
        'data': presigned_post,
        'url': posixpath.join('https://s3.amazonaws.com/', s3_bucket, file_name),
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
