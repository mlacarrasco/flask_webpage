from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO, emit
from datetime import datetime
import threading
import time
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key')
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Store for processed data
processed_data = {}

class AlarmProcessor:
    def __init__(self):
        self.latest_data = None
        self.is_running = False
        self.processing_thread = None

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
                    processed_data[processed['timestamp']] = processed
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

# Initialize processor
alarm_processor = AlarmProcessor()

@app.route('/')
def index():
    """Render the monitoring interface"""
    try:
        return render_template('monitor.html')
    except Exception as e:
        logger.error(f"Error rendering template: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'processor_running': alarm_processor.is_running
        })
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/process', methods=['POST'])
def process_json():
    """Endpoint to receive and process JSON data"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        alarm_processor.latest_data = data
        processed = alarm_processor.process_alarm_data(data)
        
        return jsonify({
            'status': 'success',
            'processed_data': processed
        })

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/history', methods=['GET'])
def get_history():
    """Endpoint to get processing history"""
    try:
        history = dict(list(processed_data.items())[-10:])  # Last 10 items
        return jsonify({
            'status': 'success',
            'history': history
        })
    except Exception as e:
        logger.error(f"Error retrieving history: {str(e)}")
        return jsonify({'error': str(e)}), 500

@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    try:
        logger.info('Client connected')
        emit('connection_response', {'status': 'connected'})
    except Exception as e:
        logger.error(f"Connection error: {str(e)}")

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    logger.info('Client disconnected')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    alarm_processor.start_processing()
    socketio.run(app, host='0.0.0.0', port=port, debug=False)