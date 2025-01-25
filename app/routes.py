from flask import render_template, request, jsonify
from datetime import datetime
from app import app, socketio, logger
from app.processor import alarm_processor

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

        # Update latest data for processing
        alarm_processor.latest_data = data

        # Immediate processing
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
        # Get query parameters
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        
        # Get history using the new AlarmHistory functionality
        history = alarm_processor.get_history(start_time, end_time)
        
        return jsonify({
            'status': 'success',
            'history': history,
            'count': len(history)
        })
    except Exception as e:
        logger.error(f"Error retrieving history: {str(e)}")
        return jsonify({'error': str(e)}), 500

@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    try:
        logger.info('Client connected')
        # Send the latest alarm data if available
        latest = alarm_processor.get_latest_alarm()
        if latest:
            socketio.emit('processed_data', latest)
        socketio.emit('connection_response', {'status': 'connected'})
    except Exception as e:
        logger.error(f"Connection error: {str(e)}")

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    logger.info('Client disconnected')