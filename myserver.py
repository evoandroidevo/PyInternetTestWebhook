import threading
import http.client as httplib
import functools
#https://devopslifecycle.com/lessons/3/receiving-webhooks-with-python
from flask import Flask, request, abort
import requests
from retry import retry

SEND_URL = "webhook here"

class NoInternet(Exception):
    """Exception for @retry"""
    pass

#https://stackoverflow.com/questions/3764291/how-can-i-see-if-theres-an-available-and-active-network-connection-in-python
def have_internet() -> bool:
    """Check for active internet connenction"""
    conn = httplib.HTTPSConnection("8.8.8.8", timeout=5)
    try:
        conn.request("HEAD", "/")
        return True
    except Exception:
        return False
    finally:
        conn.close()

def threaded(func):
    #https://stackoverflow.com/questions/67071870/python-make-a-function-always-use-a-thread-without-calling-thread-start
    """Decorator to automatically launch a function in a thread"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):  # replaces original function...
        # ...and launches the original in a thread
        thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        print("Starting Thread")
        thread.start()
        return thread
    return wrapper

app = Flask(__name__)

@threaded
@retry(NoInternet, delay=5, tries=30, backoff=30, max_delay=120)
#https://stackoverflow.com/questions/62389750/in-python-how-do-i-re-run-a-function-if-it-throws-an-error
def send_data(arg):
    """Send the webhook request to the intended destination after testing internet"""
    #used https://gist.github.com/Bilka2/5dd2ca2b6e9f3573e0c2defe5d3031b2
    #as a base for this.
    try:
        if have_internet():
            result = requests.post(SEND_URL, json=arg, timeout=5)
            if 200 <= result.status_code < 300:
                print(f"Webhook sent to discord \nReturned Code: {result.status_code}")
            else:
                print(f"Not sent with {result.status_code}, response:\n{result.json()}")
        else:
            raise NoInternet("ERROR: No Internet Detected.")
    except Exception as error:
        print(error)
        raise


@app.route('/webhook', methods=['POST'])
def webhook():
    """Webhook POST listener"""
    if request.method == 'POST':
        data = request.json
        send_data(data)
        return 'success', 200
    else:
        abort(400)

if __name__ == '__main__':
    app.run()
