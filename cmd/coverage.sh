#!/usr/bin/env bash

echo "generating coverage files"
# if I added these options to the pyproject.toml, breakpoints inside vscode would not work...
pytest --cov=big_slpp --cov-report xml
