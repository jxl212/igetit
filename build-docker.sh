#!/usr/bin/env bash

docker build --pull --rm -t igetit:latest .
docker run --name igetit --rm  igetit:latest
