Run flask app in browser:
1. `export FLASK_ENV=development`
2. `export FLASK_APP=app`
3. `flask run`

Schedule zoom.py to run daily using cron
1. Type `sudo crontab -e`
2. Add `0 0 * * * /home/[net-id]/miniconda3/bin/python /home/[net-id]/zoom-app/flask_zoom/zoom.py >> /home/[net-id]/zoom-app/flask_zoom/zoom.log 2>&1` to the end of the file, replacing [net-id] with your net-id

