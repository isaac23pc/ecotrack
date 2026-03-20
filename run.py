import os
from app import create_app

env = os.environ.get('FLASK_ENV', 'development')
app = create_app(env)

# Speed up static file delivery
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000  # 1 year cache

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=(env == 'development'), host='0.0.0.0', port=port)
