#!/bin/bash
celery -A app.tasks worker --loglevel=info
