import os
import boto3
from decimal import Decimal
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# AWS Credentials and Configuration
AWS_REGION = os.environ.get("AWS_Region", "ap-south-1")
TABLE_NAME = os.environ.get("Table_Name", "BUY_PROPERTY")
AWS_ACCESS_KEY_ID = os.environ.get("AWS_Access_Key_ID", "AKIA32VVAONMTGEJMYPW")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_Secret_Access_Key", "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")

dynamodb = boto3.resource(
    'dynamodb',
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

table = dynamodb.Table(TABLE_NAME)

# DynamoDB के Decimal डेटा को JSON में बदलने के लिए हेल्पर फंक्शन
def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj) if obj % 1 != 0 else int(obj)
    raise TypeError

def get_all_properties():
    try:
        response = table.scan()
        items = response.get('Items', [])
        # Decimal वैल्यूज को सामान्य नंबर में बदलना ताकि JSON एरर न आए
        import json
        items_str = json.dumps(items, default=decimal_default)
        return json.loads(items_str)
    except Exception as e:
        print("DynamoDB Scan Error:", e)
        return []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/search', methods=['GET'])
def search_properties():
    query = request.args.get('q', '').lower().strip()
    properties = get_all_properties()
    results = []
    
    for prop in properties:
        loc = prop.get('location', {})
        locality = str(loc.get('locality', '')).lower()
        city = str(loc.get('city', '')).lower()
        full_address = str(loc.get('full_address', '')).lower()
        title = str(prop.get('title', '')).lower()
        property_id = str(prop.get('property_id', '')).lower() # Property ID को भी स्ट्रिंग में बदला
        
        # अब सर्च में property_id भी शामिल है
        if (not query or 
            query in locality or 
            query in city or 
            query in full_address or 
            query in title or
            query in property_id):
            results.append(prop)
            
    return jsonify(results)

@app.route('/property/<property_id>')
def property_detail(property_id):
    properties = get_all_properties()
    prop = next((p for p in properties if str(p.get('property_id')) == str(property_id)), None)
    return render_template('detail.html', property=prop)

if __name__ == '__main__':
    app.run(debug=True)
    
