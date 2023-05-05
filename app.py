import time
import subprocess
from flask import Flask, render_template, Response, request, stream_with_context

import logging

app = Flask(__name__)

logger = logging.getLogger(__name__)
app.logger = logging.getLogger(__name__)

p = None  # initialize the subprocess PID variable

@app.route('/')
def index():
    return render_template('index.html')

def generate():
    with open('test.log', 'rb', buffering=0) as f:
        while True:
            line = f.readline()
            if not line:
                if p is None or p.poll() is not None:
                    break  # subprocess has finished running or not started yet
                time.sleep(1)
                continue
            yield f"{line.decode()}\n"

@app.route('/start')
def start():
    global p  # reference the global PID variable
    services = request.args.get('services')
    if services is None:
        return 'No services provided'
    service_list = services.split(',')  # convert services string to list
    p = subprocess.Popen(['python3', 'vijay.py'] + service_list, stdout=open('test.log', 'wb'))
    app.logger.info(f'Started vijay.py subprocess with services: {services}')
    return Response(generate(), mimetype='text/plain', content_type="text/event-stream")

@app.route('/stop')
def stop():
    global p  # reference the global PID variable
    if p is None:
        return 'No subprocess is running'
    p.terminate()
    app.logger.info(f'Terminated vijay.py subprocess with PID: {p.pid}')
    p = None  # reset the PID variable
    return 'Stopped'

@app.route('/logs')
def logs():
    return Response(stream_with_context(generate()), mimetype='text/plain', content_type="text/event-stream")

if __name__ == '__main__':
    app.run(debug=True)
