import os
from flask import Flask, render_template, request, jsonify
import requests
from requests.auth import HTTPBasicAuth

app = Flask(__name__)

# आपकी Test API Keys
RAZORPAY_KEY_ID = "rzp_test_TuSHYJk4OvQwda"
RAZORPAY_KEY_SECRET = "TC7QeoZfv6AO1BU5pD21zlwx"

@app.route('/')
def index():
    return render_template('index.html', key_id=RAZORPAY_KEY_ID)

@app.route('/create-order', methods=['POST'])
def create_order():
    try:
        # Razorpay Orders API को सीधे Requests के ज़रिए कॉल करना
        url = "https://api.razorpay.com/v1/orders"
        payload = {
            "amount": 50000,  # ₹500 (पैसा में)
            "currency": "INR",
            "receipt": "order_rcptid_onlybroker"
        }
        
        response = requests.post(
            url,
            json=payload,
            auth=HTTPBasicAuth(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET)
        )
        
        order_data = response.json()
        if response.status_code == 200:
            return jsonify(order_data)
        else:
            error_msg = order_data.get("error", {}).get("description", "Unknown error")
            return jsonify({"error": error_msg}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    
