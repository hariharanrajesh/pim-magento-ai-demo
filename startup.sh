#!/bin/bash
export PYTHONPATH=/home/site/wwwroot/.python_packages/lib/site-packages:$PYTHONPATH
python -m uvicorn src.app:app --host 0.0.0.0 --port 8000