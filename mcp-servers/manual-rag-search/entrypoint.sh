#!/bin/sh
set -e
python build_index.py
exec python server.py
