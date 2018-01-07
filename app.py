from flask import Flask, render_template, request, redirect, url_for
import os, json, boto3
from settings import *

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('home.html')


# Listen for POST requests to yourdomain.com/submit_form/
@app.route("/submit-form/", methods = ["POST"])
def submit_form():

  # Collect the data posted from the HTML form in account.html:
  avatar_url = request.form["avatar-url"]

  # Provide some procedure for storing the new details
  # update_account(username, full_name, avatar_url)

  # For now, we'll just load homepage again.
  return render_template('home.html'), 201


# Listen for GET requests to yourdomain.com/sign_s3/
#
# Please see https://gist.github.com/RyanBalfanz/f07d827a4818fda0db81 for an example using
# Python 3 for this view.
@app.route('/sign-s3/')
def sign_s3():
  # Load necessary information into the application
  S3_BUCKET = os.environ.get('S3_BUCKET')

  # Load required data from the request
  file_name = request.args.get('file-name')
  file_type = request.args.get('file-type')

  # Initialise the S3 client
  s3 = boto3.client('s3')

  # Generate and return the presigned URL
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

  # Return the data to the client
  return json.dumps({
    'data': presigned_post,
    'url': 'https://%s.s3.amazonaws.com/%s' % (S3_BUCKET, file_name)
  })


# Main code
if __name__ == '__main__':
  port = int(os.environ.get('PORT', 5000))
  app.run(host='0.0.0.0', port = port)
