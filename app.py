from api import blueprint
from config import app

if __name__ == "__main__":
    app.register_blueprint(blueprint, url_prefix="/api_v1")
    app.run(debug=True, port=8001)
