from app import app, socketio
from app.processor import alarm_processor

if __name__ == "__main__":
    alarm_processor.start_processing()
    socketio.run(app, debug=False)