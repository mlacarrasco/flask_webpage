from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from datetime import datetime
import threading
import time
import logging
from flask import render_template

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Store for processed data
processed_data = {}

class AlarmProcessor:
    def __init__(self):
        self.latest_data = None
        self.is_running = False
        self.processing_thread = None
        self.threshold = 60.0  # Set threshold for alarma.X

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
                    logger.info(f"Processed alarm data: {processed}")
                except Exception as e:
                    logger.error(f"Error processing data: {str(e)}")
            time.sleep(1)

    def process_alarm_data(self, data):
        """Process alarm data and add additional information"""
        try:
            # Extract the alarma.X value
            alarm_value = data.get('evaluation', {}).get('last_values', {}).get('alarma.X')
            
            processed = {
                'timestamp': datetime.now().isoformat(),
                'device_id': data.get('origin', {}).get('id', 'unknown'),
                'alarm_name': data.get('name', ''),
                'alarm_rule': data.get('alarm', {}).get('rule'),
                'activation_time': data.get('activation', {}).get('completed'),
                'created_time': data.get('created'),
                'modified_time': data.get('modified'),
                'detections': data.get('activation', {}).get('detections'),
                'alarm_value': alarm_value,
                'instance': data.get('instance'),
                'severity': data.get('severity'),
                'state': data.get('state'),
                'status': 'active' if data.get('state') == 1 else 'inactive',
                'source': data.get('origin', {}).get('source'),
            }
            
            # Add threshold analysis
            if alarm_value is not None:
                processed.update({
                    'threshold_exceeded': alarm_value > self.threshold,
                    'threshold_value': self.threshold,
                    'threshold_difference': alarm_value - self.threshold
                })
            
            return processed
        except Exception as e:
            logger.error(f"Error in process_alarm_data: {str(e)}")
            raise

# Initialize processor
alarm_processor = AlarmProcessor()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'processor_running': alarm_processor.is_running
    })

@app.route('/process', methods=['POST'])
def process_json():
    """Endpoint to receive and process JSON data"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Validate required fields
        required_fields = ['activation', 'alarm', 'evaluation']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({'error': f'Missing required fields: {missing_fields}'}), 400

        # Update latest data for processing
        alarm_processor.latest_data = data

        # Immediate processing response
        processed = alarm_processor.process_alarm_data(data)
        
        return jsonify({
            'status': 'success',
            'processed_data': processed,
            'original_data': data
        })

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/history', methods=['GET'])
def get_history():
    """Endpoint to get processing history"""
    try:
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        device_id = request.args.get('device_id')
        
        history = processed_data.copy()
        
        # Apply filters
        if start_time:
            history = {k: v for k, v in history.items() if k >= start_time}
        if end_time:
            history = {k: v for k, v in history.items() if k <= end_time}
        if device_id:
            history = {k: v for k, v in history.items() if v.get('device_id') == device_id}
            
        return jsonify({
            'status': 'success',
            'history': history,
            'total_records': len(history)
        })
    except Exception as e:
        logger.error(f"Error retrieving history: {str(e)}")
        return jsonify({'error': str(e)}), 500



# Add this route to your Flask app
@app.route('/template')
def index():
    return render_template('monitor.html')

@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    logger.info('Client connected')
    emit('connection_response', {
        'status': 'connected',
        'timestamp': datetime.now().isoformat()
    })

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    logger.info('Client disconnected')

def start_server():
    """Start the Flask server with WebSocket support"""
    alarm_processor.start_processing()
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)

if __name__ == '__main__':
    start_server()

# Example test with the provided JSON:
"""
curl -X POST http://localhost:5000/process \
     -H "Content-Type: application/json" \
     -d '{
       "activation":{"completed":1737647372491,"detections":1,"initiated":1737647372491},
       "alarm":{"group":"","rule":"alarma_3","type":""},
       "evaluation":{"last_completed":1737647372491,"last_values":{"alarma.X":60.3}},
       "instance":"A3-243293886",
       "origin":{"id":"Seed_XIAO_nRF52","name":"","source":"device"},
       "severity":2,
       "state":1
     }'
"""