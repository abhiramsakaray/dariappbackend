import os
import base64

logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logo.png')
with open(logo_path, 'rb') as f:
    logo_data = f.read()
logo_base64 = base64.b64encode(logo_data).decode('utf-8')

with open(os.path.join(os.path.dirname(__file__), 'logo_base64.txt'), 'w') as f:
    f.write(logo_base64)
