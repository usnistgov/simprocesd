#!/bin/bash

SCRIPTPATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

# Do some cleaning.
rm -rf "$SCRIPTPATH/build"
mkdir "$SCRIPTPATH/build"
cp "$SCRIPTPATH/.nojekyll" "$SCRIPTPATH/build/.nojekyll"

# Building directly into ./ prevents custom.css from applying.
sphinx-build -E -b html "$SCRIPTPATH/docs/source/" "$SCRIPTPATH/build/"
