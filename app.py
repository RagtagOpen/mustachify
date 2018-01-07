from flask import Flask, render_template, request, redirect, url_for
import os, json, boto3
from settings import *

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('home.html')

@app.route("/submit-form/", methods = ["POST"])
def submit_form():

  # Collect the data posted from the HTML form
  avatar_url = request.form["avatar-url"]
  # TODO: Send this over to Rekognition API

  # For now, we'll just load homepage again.
  return render_template('home.html'), 201


@app.route('/sign-s3/')
def sign_s3():
  S3_BUCKET = os.environ.get('S3_BUCKET')
  file_name = request.args.get('file-name')
  file_type = request.args.get('file-type')

  s3 = boto3.client('s3')

  presigned_post = s3.generate_presigned_post(
    Bucket = S3_BUCKET,
    Key = file_name,
    Fields = {"acl": "public-read", "Content-Type": file_type},
    Conditions = [
      {"acl": "public-read"},
      {"Content-Type": file_type}
    ],
    ExpiresIn = 3600
  )

  return json.dumps({
    'data': presigned_post,
    'url': 'https://%s.s3.amazonaws.com/%s' % (S3_BUCKET, file_name)
  })


if __name__ == '__main__':
  port = int(os.environ.get('PORT', 5000))
  app.run(host='0.0.0.0', port = port)
