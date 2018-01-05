import argparse
import boto3
import io
import json
import os
import pprint
import requests
import shutil
from PIL import Image, ImageDraw


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('image', type=argparse.FileType('rb'),
                        help='the image to apply the mustache to')

    args = parser.parse_args()

    # Load image into memory
    print("Load image")
    buf = io.BytesIO()
    shutil.copyfileobj(args.image, buf)
    buf.seek(0)

    # Send image to AWS and detect faces
    print("Detect image")
    cache_filename = args.image.name + '.resultcache'
    if os.path.exists(cache_filename):
        print("... Reusing cached results at", cache_filename)
        with open(cache_filename, 'r') as f:
            response = json.load(f)

    else:
        print("... Caching Rekognition results to", cache_filename)
        rekognition = boto3.client("rekognition", 'us-east-1')
        response = rekognition.detect_faces(
            Image={
                'Bytes': buf.getvalue()
            },
        )

        with open(cache_filename, 'w') as f:
            json.dump(response, f)

    assert response['FaceDetails'], "No faces detected"
    first_face = response['FaceDetails'][0]

    # Open the image to apply the mustache to
    im = Image.open(buf)

    # Push the landmarks into a dict so its easier to interact with them
    landmarks = dict([
        (l['Type'], (int(l['X'] * im.size[0]), int(l['Y'] * im.size[1])))
        for l in first_face.get('Landmarks')
    ])

    # Mark landmarks in the image
    def mark_spot(draw, x, y, r=2):
        draw.ellipse((x - r, y - r, x + r, y + r), fill='red')

    # draw = ImageDraw.Draw(im)
    # mark_spot(draw, landmarks['mouthLeft'][0], landmarks['mouthLeft'][1])
    # mark_spot(draw, landmarks['mouthRight'][0], landmarks['mouthRight'][1])
    # mark_spot(draw, landmarks['nose'][0], landmarks['nose'][1])
    # del draw

    # Load the mustache image
    mustache_im = Image.open('mustache_test.png')

    # Find the right spot to place the mustache
    nose_x, nose_y = landmarks['nose']
    mleft_x, mleft_y = landmarks['mouthLeft']
    mright_x, mright_y = landmarks['mouthRight']
    new_mustache_size = (mright_x - mleft_x, mleft_y - nose_y)
    mustache_im = mustache_im.resize(new_mustache_size)
    im.paste(mustache_im, (mleft_x, mleft_y - new_mustache_size[1]), mustache_im)
    print("Showing you the image with an image viewer")
    im.show()


if __name__ == '__main__':
    main()
