import os
import json
from decimal import Decimal
from flask import Flask, render_template, request, jsonify
import boto3

app = Flask(__name__)

# AWS Configuration using Environment Variables
# Agar environment variable set nahi hai, toh default region 'ap-south-1' use hoga
AWS_REGION = os.environ.get("AWS_REGION", "ap-south-1")
TABLE_NAME = os.environ.get("TABLE_NAME", "BUY_PROPERTY")

# Best Practice: Access Key aur Secret Key ko hardcode na karein.
# Boto3 apne aap environment variables (AWS_ACCESS_KEY_ID aur AWS_SECRET_ACCESS_KEY) 
# ya EC2/Lambda IAM Roles se credentials utha leta hai.
aws_access_key_id = os.environ.get("AWS_ACCESS_KEY_ID")
aws_secret_access_key = os.environ.get("AWS_SECRET_ACCESS_KEY")

# DynamoDB Resource initialization
if aws_access_key_id and aws_secret_access_key:
    dynamodb = boto3.resource(
        'dynamodb',
        region_name=AWS_REGION,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key
    )
else:
    # Agar keys explicitly pass nahi karni, toh boto3 default credential chain use karega
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)

table = dynamodb.Table(TABLE_NAME)

# DynamoDB ke Decimal डेटा को JSON में बदलने के लिए हेल्पर फंक्शन
def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj) if obj % 1 != 0 else int(obj)
    raise TypeError

def get_all_properties():
    try:
        response = table.scan()
        items = response.get('Items', [])
        # Decimal वैल्यूज को सामान्य नंबर में बदलना ताकि JSON एरर न आए
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
        property_id = str(prop.get('property_id', '')).lower()
        
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
    
