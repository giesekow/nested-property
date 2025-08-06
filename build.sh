#!/bin/bash

rm -rf build
rm -rf dist
rm -rf *.egg-info
#python3 -m build
./venv/bin/python setup.py sdist
./venv/bin/python setup.py bdist_wheel