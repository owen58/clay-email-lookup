import os
import uuid
import requests
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Store results temporarily (in production, use Redis or a database)
results_store = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/lookup', methods=['POST'])
def lookup():
    data = request.get_json()

    # Validate required fields
    full_name = data.get('fullName')
    company_name = data.get('companyName')
    company_domain = data.get('companyDomain')
    linkedin_url = data.get('linkedinUrl')

    if not full_name or not company_name or not company_domain:
        return jsonify({'error': 'Missing required fields'}), 400

    webhook_url = os.getenv('CLAY_WEBHOOK_URL')
    if not webhook_url:
        return jsonify({'error': 'Server configuration error'}), 500

    # Generate unique ID to track this request
    request_id = str(uuid.uuid4())
    results_store[request_id] = {'status': 'pending'}

    # Send to Clay with the request ID so Clay can send it back
    try:
        clay_response = requests.post(
            webhook_url,
            json={
                'requestId': request_id,
                'fullName': full_name,
                'companyName': company_name,
                'companyDomain': company_domain,
                'linkedinUrl': linkedin_url,
            },
            headers={'Content-Type': 'application/json'}
        )
        print(f'Clay response: {clay_response.status_code} {clay_response.text}')
    except requests.RequestException as e:
        print(f'Clay webhook error: {e}')
        return jsonify({'error': 'Failed to contact Clay'}), 502

    return jsonify({'requestId': request_id})

@app.route('/api/results', methods=['POST'])
def receive_results():
    """Clay sends results here"""
    data = request.get_json()
    print(f'Received from Clay: {data}')

    request_id = data.get('requestId')
    if request_id and request_id in results_store:
        results_store[request_id] = {
            'status': 'complete',
            'email': data.get('email') or data.get('Email'),
            'data': data
        }

    return jsonify({'success': True})

@app.route('/api/results/<request_id>', methods=['GET'])
def get_results(request_id):
    """Frontend polls this to get results"""
    result = results_store.get(request_id, {'status': 'not_found'})
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True, port=3000)
