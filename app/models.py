from datetime import datetime
from typing import Dict, Any, Optional

class AlarmData:
    """Class to represent and validate alarm data"""
    def __init__(self, data: Dict[str, Any]):
        self.raw_data = data
        self.timestamp = datetime.now()
        
        # Extract data with validation
        self.activation = self._get_activation()
        self.alarm = self._get_alarm()
        self.evaluation = self._get_evaluation()
        self.instance = data.get('instance', '')
        self.severity = data.get('severity', 0)
        self.state = data.get('state', 0)
        self.origin = self._get_origin()

    def _get_activation(self) -> Dict[str, Any]:
        """Extract and validate activation data"""
        activation = self.raw_data.get('activation', {})
        return {
            'completed': activation.get('completed'),
            'detections': activation.get('detections', 0),
            'initiated': activation.get('initiated')
        }

    def _get_alarm(self) -> Dict[str, Any]:
        """Extract and validate alarm data"""
        alarm = self.raw_data.get('alarm', {})
        return {
            'group': alarm.get('group', ''),
            'rule': alarm.get('rule', ''),
            'type': alarm.get('type', '')
        }

    def _get_evaluation(self) -> Dict[str, Any]:
        """Extract and validate evaluation data"""
        evaluation = self.raw_data.get('evaluation', {})
        return {
            'last_completed': evaluation.get('last_completed'),
            'last_values': evaluation.get('last_values', {})
        }

    def _get_origin(self) -> Dict[str, Any]:
        """Extract and validate origin data"""
        origin = self.raw_data.get('origin', {})
        return {
            'id': origin.get('id', ''),
            'name': origin.get('name', ''),
            'source': origin.get('source', '')
        }

    def get_alarm_value(self) -> Optional[float]:
        """Get the alarma.X value if it exists"""
        try:
            return self.evaluation['last_values'].get('alarma.X')
        except (KeyError, AttributeError):
            return None

    def is_active(self) -> bool:
        """Check if the alarm is active"""
        return self.state == 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert alarm data to dictionary format"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'device_id': self.origin['id'],
            'alarm_rule': self.alarm['rule'],
            'activation_time': self.activation['completed'],
            'detections': self.activation['detections'],
            'alarm_value': self.get_alarm_value(),
            'instance': self.instance,
            'severity': self.severity,
            'status': 'active' if self.is_active() else 'inactive',
            'source': self.origin['source']
        }

class ProcessedAlarm:
    """Class to represent processed alarm data"""
    def __init__(self, alarm_data: AlarmData):
        self.alarm_data = alarm_data
        self.processed_at = datetime.now()
        self.threshold = 60.0  # Default threshold

    def get_processed_data(self) -> Dict[str, Any]:
        """Get processed alarm data with additional analysis"""
        alarm_value = self.alarm_data.get_alarm_value()
        base_data = self.alarm_data.to_dict()
        
        # Add processing-specific fields
        base_data.update({
            'processed_at': self.processed_at.isoformat(),
            'threshold_exceeded': alarm_value > self.threshold if alarm_value is not None else None,
            'threshold_value': self.threshold,
            'threshold_difference': alarm_value - self.threshold if alarm_value is not None else None
        })
        
        return base_data

class AlarmHistory:
    """Class to manage alarm history"""
    def __init__(self, max_size: int = 100):
        self.history: Dict[str, Dict[str, Any]] = {}
        self.max_size = max_size

    def add_alarm(self, processed_alarm: ProcessedAlarm):
        """Add a processed alarm to history"""
        data = processed_alarm.get_processed_data()
        self.history[data['timestamp']] = data
        
        # Remove oldest entries if exceeding max size
        if len(self.history) > self.max_size:
            oldest_key = min(self.history.keys())
            del self.history[oldest_key]

    def get_history(self, start_time: Optional[str] = None, end_time: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """Get filtered history"""
        history = self.history.copy()
        
        if start_time:
            history = {k: v for k, v in history.items() if k >= start_time}
        if end_time:
            history = {k: v for k, v in history.items() if k <= end_time}
            
        return history

    def clear_history(self):
        """Clear all history"""
        self.history.clear()

    def get_latest(self) -> Optional[Dict[str, Any]]:
        """Get the most recent alarm data"""
        if not self.history:
            return None
        latest_key = max(self.history.keys())
        return self.history[latest_key]