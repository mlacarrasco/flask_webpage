from datetime import datetime
import threading
import time
from app import socketio, logger
from app.models import AlarmData, ProcessedAlarm, AlarmHistory

class AlarmProcessor:
    def __init__(self):
        self.latest_data = None
        self.is_running = False
        self.processing_thread = None
        self.alarm_history = AlarmHistory(max_size=100)

    def start_processing(self):
        if not self.is_running:
            self.is_running = True
            self.processing_thread = threading.Thread(target=self.process_data_continuously)
            self.processing_thread.start()

    def stop_processing(self):
        self.is_running = False
        if self.processing_thread:
            self.processing_thread.join()

    def process_data_continuously(self):
        while self.is_running:
            if self.latest_data:
                try:
                    processed = self.process_alarm_data(self.latest_data)
                    socketio.emit('processed_data', processed)
                    self.alarm_history.add_alarm(processed)
                except Exception as e:
                    logger.error(f"Error in continuous processing: {str(e)}")
            time.sleep(1)

    def process_alarm_data(self, data):
        """Process alarm data using models"""
        try:
            # Create AlarmData instance for validation and structuring
            alarm_data = AlarmData(data)
            
            # Create ProcessedAlarm instance for additional processing
            processed_alarm = ProcessedAlarm(alarm_data)
            
            return processed_alarm.get_processed_data()
        except Exception as e:
            logger.error(f"Error processing alarm data: {str(e)}")
            raise

    def get_history(self, start_time=None, end_time=None):
        """Get processed alarm history"""
        return self.alarm_history.get_history(start_time, end_time)

    def get_latest_alarm(self):
        """Get the most recent alarm"""
        return self.alarm_history.get_latest()

# Create a global instance
alarm_processor = AlarmProcessor()