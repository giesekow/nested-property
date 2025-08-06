#!/bin/bash

rm -rf venv

python3 -m virtualenv venv
./venv/bin/pip install wheel twine