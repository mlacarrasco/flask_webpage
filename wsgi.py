import eventlet
eventlet.monkey_patch()

from app import app, socketio
from app.processor import alarm_processor

if __name__ == "__main__":
    alarm_processor.start_processing()
    socketio.run(app, host='0.0.0.0', port=10000)