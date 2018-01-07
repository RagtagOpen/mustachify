# Mustachify

Apply a mustache to an image containing a face using AWS's Rekognition API.

The basic process is
1. User uploads photo, which is saved to S3
2. The app sends the file from S3 to Amazon's Rekongition API, adds a mustache, and saves the modified image back to the S3 bucket
3. The app displays the 'stached image.
4. The app destros the original and 'stached images from the S3 bucket.

## Local Development

Before you start, you'll need to create an S3 bucket and provide credentials in your development environment.
I used a `.env` file. There's a sample .env file located at the root directory of this project, in case you
want an example.

For directions on CORS config, feel free to consult the toturial mentioned in the
Contributors section of this README.

This project uses pipenv to manage depdendencies.  Run he following commands.

```
pipenv install # download dependencies
pipenv shell # activate the project's virtualenv
```

Once you have the dependencies installed, run the following command in terminal:

```
$ export FLASK_APP=app.py
$ flask run
```

In your browser, nagivate to `localhost:5000/` to see the site.


## Contributors

This codebase was begun by cobbling together info from the [Flask Quickstart Guide](http://flask.pocoo.org/docs/0.12/quickstart/)
and this [S3 direct upload tutorial](https://devcenter.heroku.com/articles/s3-upload-python).

In other words, if you're reading this, then you probably know more about Python and Flask best practices than I do.
So feel free to modify, remove, or add any code you feel is necessary.

## ToDo
1. Integrate Reckognition and stachification code into Flask app.
2. Layer in some CSS to provide a better UX

