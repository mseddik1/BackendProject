import time

print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] TESTING CRONJOB")

#*/1 * * * * /usr/bin/python3 "/Users/mseddik/IdeaProjects/Backend Project I/src/app/cronjobs/test_cron.py" >> "/Users/mseddik/IdeaProjects/Backend Project I/logs/test_cron.log" 2>&1