#!/bin/bash

SCRIPTPATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

ls $SCRIPTPATH/docs/build/

# Building directly into ./ prevents custom.css from applying.
sphinx-build -E -b html $SCRIPTPATH/docs/source/ $SCRIPTPATH/docs/build/

# Do some cleaning.
rm -rf $SCRIPTPATH/_sources
rm -rf $SCRIPTPATH/_static

# Move build files to root for pages to pick it up.
mv $SCRIPTPATH/docs/build/* $SCRIPTPATH
