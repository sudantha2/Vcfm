from flask import Flask
from threading import Thread
import os

app = Flask('')

@app.route('/')
def home():
    return "ðŸŽµ FM Player Bot is running!"

@app.route('/health')
def health():
    return {"status": "healthy", "service": "fm_player_bot"}

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()
