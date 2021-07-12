Set up flask app to run using gunicorn:
1. Type `sudo vim /etc/nginx/sites-available/default` (you can use nano if your prefer)
2. Delete the entire `try` statement (it's just one line) under "location /", keep everything else the same
3. Restart nginx with `sudo systemctl reload nginx`
4. Add a file called "vcmconfig.py" to the flask_zoom directory
5. In that file write `VCM = "https://vcm-[#].vm.duke.edu/"`, replacing [#] with your vcm number

Run flask app using gunicorn:
1. `gunicorn -w 4 app:app --reload`

Schedule zoom.py to run daily using cron
1. Type `sudo crontab -e`
2. Add `0 0 * * * /home/[net-id]/miniconda3/bin/python /home/[net-id]/zoom-app/flask_zoom/zoom.py >> /home/[net-id]/zoom-app/flask_zoom/zoom.log 2>&1` to the end of the file, replacing [net-id] with your net-id
3. 

Run flask app in browser (won't work anymore):
1. `export FLASK_ENV=development`
2. `export FLASK_APP=app`
3. `flask run`