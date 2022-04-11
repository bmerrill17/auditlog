from flask import Flask
from flask_restful import Api
import endpoints

if __name__ == '__main__':
    # creates the API based on the Flask framework
    app = Flask(__name__)
    api = Api(app)

    # adds each API endpoint with specified URL based on the classes in endpoints
    api.add_resource(endpoints.Log, '/logs/<string:api_key>/<int:event_id>')
    api.add_resource(endpoints.AllLogs, '/logs/<string:api_key>')
    api.add_resource(endpoints.QueryLogs, '/logs/<string:api_key>/query')

    # runs the API
    app.run(host='0.0.0.0')
