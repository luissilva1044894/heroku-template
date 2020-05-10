web: hypercorn -b 0.0.0.0:${PORT} app:app
gunicorn: gunicorn --worker-class quart.worker.GunicornWorker app:app
gunicorn_uvicorn: gunicorn -b 0.0.0.0:$PORT app:app -w 4 -k uvicorn.workers.UvicornWorker
uvicorn: uvicorn app:app --host 0.0.0.0 --port $PORT
