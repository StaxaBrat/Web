python app.py
#!/bin/sh
gunicorn -w 4 -b 0.0.0.0:$PORT app:app
gunicorn app:app --bind 0.0.0.0:$PORT
