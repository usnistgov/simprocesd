#!/bin/bash

# Building directly into ./ prevents custom.css from applying.
sphinx-build -E -b html docs/source/ docs/build/

# Do some cleaning.
rm -rf _sources
rm -rf _static

# Move build files to root for pages to pick it up.
mv docs/build/* .
