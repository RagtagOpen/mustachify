# Mustachify

Apply a mustache to an image containing a face using AWS's Rekognition API.

The basic process is
1. User uploads photo, which is saved to S3
2. The app sends the file from S3 to Amazon's Rekongition API, adds a mustache, and saves the modified image back to the S3 bucket
3. The app displays the 'stached image.
4. The app destroys the original and 'stached images from the S3 bucket.

## Local Development

Before you start, you'll need to create an S3 bucket and provide credentials in your development environment. I used a `.env` file. There's a sample `.env` file located at the root directory of this project, in case you want an example.

The S3 bucket you use must have a properly configured CORS setup to allow direct uploads. Follow the [S3 section in the Heroku tutorial](https://devcenter.heroku.com/articles/s3-upload-python#s3-setup) to make sure your bucket is properly configured.

This project uses pipenv to manage depdendencies. Run the following commands.

```
pipenv install # download dependencies
pipenv shell # activate the project's virtualenv
```

Once you have the dependencies installed, run the following command in terminal:

```
$ FLASK_APP=app.py flask run
```

In your browser, nagivate to [http://localhost:5000/](http://localhost:5000/) to see the site.


## More Links

This codebase was begun by cobbling together info from the [Flask Quickstart Guide](http://flask.pocoo.org/docs/0.12/quickstart/) and this [S3 direct upload tutorial](https://devcenter.heroku.com/articles/s3-upload-python).
