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
        self.alarm_history = AlarmHistory(max_size=1000)

    def start_processing(self):
        if not self.is_running:
            self.is_running = True
            self.processing_thread = threading.Thread(target=self.process_data_continuously)
            self.processing_thread.start()
            logger.info("Alarm processor started")

    def stop_processing(self):
        self.is_running = False
        if self.processing_thread:
            self.processing_thread.join()
            logger.info("Alarm processor stopped")

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
        try:
            processed = {
                'timestamp': datetime.now().isoformat(),
                'device_id': data.get('origin', {}).get('id', 'unknown'),
                'alarm_rule': data.get('alarm', {}).get('rule'),
                'activation_time': data.get('activation', {}).get('completed'),
                'detections': data.get('activation', {}).get('detections'),
                'alarm_value': data.get('evaluation', {}).get('last_values', {}).get('alarma.X'),
                'instance': data.get('instance'),
                'severity': data.get('severity'),
                'status': 'active' if data.get('state') == 1 else 'inactive'
            }
            return processed
        except Exception as e:
            logger.error(f"Error processing alarm data: {str(e)}")
            raise

    def get_history(self, start_time=None, end_time=None, device_id=None, 
                   severity=None, status=None, limit=10):
        """Get filtered alarm history"""
        try:
            return self.alarm_history.get_history(
                start_time=start_time,
                end_time=end_time,
                device_id=device_id,
                severity=severity,
                status=status,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Error getting history: {str(e)}")
            return {}

    def get_latest_alarm(self):
        """Get the most recent alarm"""
        return self.alarm_history.get_latest()