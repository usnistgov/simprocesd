#!/bin/bash

SCRIPTPATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

# Building directly into ./ prevents custom.css from applying.
sphinx-build -E -b html $SCRIPTPATH/docs/source/ $SCRIPTPATH/docs/build/

# Do some cleaning.
rm -rf $SCRIPTPATH/.doctrees
rm -rf $SCRIPTPATH/_images
rm -rf $SCRIPTPATH/_sources
rm -rf $SCRIPTPATH/_static
rm -rf $SCRIPTPATH/api_docs

# Move build files+folders to root so pages picks it up.
mv $SCRIPTPATH/docs/build/{*,.[^.]*} $SCRIPTPATH/
