from flask import Flask, request, jsonify
import json
from google.cloud import storage

app = Flask(__name__)

BUCKET_NAME = 'banking-data-json'

def download_json_from_gcs(bucket_name, file_name):
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(file_name)
    content = blob.download_as_text()
    return json.loads(content)

@app.route('/get-accounts', methods=['GET', 'POST'])
def get_accounts():
    try:
        # Try to get phone number from query param first
        phone_number = request.args.get('phone')

        # If not in query, try from JSON body
        if not phone_number:
            try:
                data = request.get_json(force=True)
                phone_number = data.get('phone')
            except Exception:
                pass  # continue if body is invalid or missing

        if not phone_number:
            return jsonify({'error': 'Phone number not provided in query or JSON body'}), 400

        # Load data from GCS
        accounts_data = download_json_from_gcs(BUCKET_NAME, 'accounts.json')
        customers_data = download_json_from_gcs(BUCKET_NAME, 'customers.json')

        # Filter customers by phone number
        target_customers = {
            customer['customer_id']
            for customer in customers_data
            if str(customer.get('phone_number')) == str(phone_number)
        }

        filtered_accounts = [
            {
                'account_number': account['account_number'],
                'balance': account['balance']
            }
            for account in accounts_data
            if account['customer_id'] in target_customers
        ]

        return jsonify(filtered_accounts), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Required for Railway or gunicorn to detect app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)