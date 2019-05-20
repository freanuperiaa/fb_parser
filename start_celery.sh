#!/bin/sh
celery -A config worker --loglevel=ERROR
