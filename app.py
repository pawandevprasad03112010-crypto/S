import os
from flask import Flask, render_template, request, jsonify
import razorpay

app = Flask(__name__)

# आपके स्क्रीनशॉट से ली गई टेस्ट की (API Keys) यहाँ जोड़ी गई हैं
RAZORPAY_KEY_ID = "rzp_test_TuSHYJk4OvQwda"
RAZORPAY_KEY_SECRET = "TC7QeoZfv6A01BU5pD21zlwx"

# Razorpay क्लाइंट को इनिशियलाइज करें
client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

@app.route('/')
def index():
    return render_template('index.html', key_id=RAZORPAY_KEY_ID)

@app.route('/create-order', methods=['POST'])
def create_order():
    try:
        # ₹500 (50000 paise) का टेस्ट आर्डर सेट किया गया है
        data = {
            "amount": 50000, 
            "currency": "INR", 
            "receipt": "order_rcptid_onlybroker"
        }
        order = client.order.create(data=data)
        return jsonify(order)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    
