from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from datetime import datetime
import threading
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
#app = Flask(__name__)
#app.config['SECRET_KEY'] = 'your-secret-key'
#socketio = SocketIO(app, cors_allowed_origins="*")

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
                    # Process the alarm data
                    processed = self.process_alarm_data(self.latest_data)
                    # Emit processed data through WebSocket
                    socketio.emit('processed_data', processed)
                    # Store processed data
                    processed_data[processed['timestamp']] = processed
                except Exception as e:
                    logger.error(f"Error processing data: {str(e)}")
            time.sleep(1)  # Process every second

    def process_alarm_data(self, data):
        """Process alarm data and add additional information"""
        try:
            processed = {
                'timestamp': datetime.now().isoformat(),
                'alarm_rule': data.get('alarm', {}).get('rule'),
                'activation_time': data.get('activation', {}).get('completed'),
                'detections': data.get('activation', {}).get('detections'),
                'alarm_value': data.get('evaluation', {}).get('last_values', {}).get('alarma.X'),
                'instance': data.get('instance'),
                'severity': data.get('severity'),
                'status': 'active' if data.get('state') == 1 else 'inactive'
            }
            
            # Add additional processing logic here
            if processed['alarm_value'] is not None:
                processed['threshold_exceeded'] = processed['alarm_value'] > 70
                
            return processed
        except Exception as e:
            logger.error(f"Error in process_alarm_data: {str(e)}")
            raise

# Initialize processor
alarm_processor = AlarmProcessor()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/process', methods=['POST'])
def process_json():
    """Endpoint to receive and process JSON data"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Update latest data for processing
        alarm_processor.latest_data = data

        # Immediate processing response
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
        # Optional query parameters for filtering
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        
        history = processed_data.copy()
        
        if start_time:
            history = {k: v for k, v in history.items() if k >= start_time}
        if end_time:
            history = {k: v for k, v in history.items() if k <= end_time}
            
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
    logger.info('Client connected')
    emit('connection_response', {'status': 'connected'})

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

# Example usage with curl:
"""
curl -X POST http://localhost:5000/process \
     -H "Content-Type: application/json" \
     -d '{
       "activation":{"completed":1737044983949,"detections":1,"initiated":1737044983949},
       "alarm":{"group":"","rule":"alarma_3","type":""},
       "evaluation":{"last_completed":1737044983949,"last_values":{"alarma.X":73.9}},
       "instance":"A3-2659422446",
       "severity":2,
       "state":1
     }'
"""