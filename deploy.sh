#!/bin/sh

FUNC=game-api
OBJECTS="tupelo gcloud-function/* .gcloudignore"
mkdir -p build
cp -a $OBJECTS build

(cd build; gcloud functions deploy "$FUNC" --runtime python37 --trigger-http --allow-unauthenticated --entry-point handler)
