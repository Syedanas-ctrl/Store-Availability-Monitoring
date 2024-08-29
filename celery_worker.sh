#!/bin/bash
celery -A app.tasks worker --loglevel=info &
celery -A app.tasks beat --loglevel=info
