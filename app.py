import os
import requests
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

CLAY_WEBHOOK_URL = "https://api.clay.com/v3/sources/webhook/pull-in-data-from-a-webhook-92b1ff24-b8c9-4217-bf77-659955339e91"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/lookup', methods=['POST'])
def lookup():
    data = request.get_json()

    full_name = data.get('fullName')
    company_name = data.get('companyName')
    company_domain = data.get('companyDomain')
    linkedin_url = data.get('linkedinUrl')

    if not full_name or not company_name or not company_domain:
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        clay_response = requests.post(
            CLAY_WEBHOOK_URL,
            json={
                'fullName': full_name,
                'companyName': company_name,
                'companyDomain': company_domain,
                'linkedinUrl': linkedin_url,
            },
            headers={'Content-Type': 'application/json'}
        )
        print(f'Clay response: {clay_response.status_code} {clay_response.text}')

        if clay_response.ok:
            return jsonify({'success': True, 'message': 'Submitted to Clay!'})
        else:
            return jsonify({'error': 'Failed to submit to Clay'}), 502

    except requests.RequestException as e:
        print(f'Clay webhook error: {e}')
        return jsonify({'error': 'Failed to contact Clay'}), 502

@app.route('/api/results', methods=['POST'])
def receive_results():
    """Endpoint for Clay to POST results back"""
    data = request.get_json()
    print(f'Received from Clay: {data}')
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True, port=3000)
