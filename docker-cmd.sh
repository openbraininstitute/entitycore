#!/bin/bash
set -ex -o pipefail

HOST=${HOST:-127.0.0.1}
PORT=${PORT:-8000}

# use exec to replace the shell and ensure that SIGINT is sent to the app
exec python -m app run --host $HOST --port $PORT
