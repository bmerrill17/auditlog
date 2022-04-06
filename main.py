from flask import Flask, request, jsonify
import datetime as dt
from flask_restful import Resource, Api, reqparse, abort
import pandas as pd

logs = pd.DataFrame(
    [{"timestamp": str(dt.datetime.now()), "source": "Salesforce", "log_text": "billed for Ubuntu Advantage",
     "customer_id": '84084', "bill_amount": 1999.99}])

app = Flask(__name__)
api = Api(app)


def check_existence(event_id):
    if int(event_id) not in logs.index.tolist():
      abort(404, message="event_id: {} doesn't exist".format(event_id))


class AllLogs(Resource):
    def get(self):
        data = logs
        data = data.to_dict()
        return {'data': data}, 200

    def post(self):
        global logs

        new_data = {"timestamp": str(dt.datetime.now())}

        for key, value in request.args.items():
            new_data[key] = value

        required_fields = ["source", "log_text"]

        for field in required_fields:
            if field not in new_data.keys():
                abort(400, message="required field: {} is missing".format(field))

        logs = logs.append(new_data, ignore_index=True)
        return {'data': logs.to_dict()}, 200

class Log(Resource):
    def get(self, event_id):
        check_existence(event_id)
        data = logs.iloc[[int(event_id)]]
        data = data.to_dict()
        return {'data': data}, 200

    def delete(self, event_id):
        check_existence(event_id)

        global logs

        logs = logs.drop(index=int(event_id))

        return {'data': logs.to_dict()}, 200

class QueryLogs(Resource):
    def get(self):

        data = logs

        for key, value in request.args.items():
            if key not in data.columns.tolist():
                abort(404, message="parameter: {} doesn't exist".format(key))
            data = data[data[key] == value]

        data = data.to_dict()

        return {'data': data}, 200

api.add_resource(Log, '/logs/<int:event_id>')
api.add_resource(AllLogs, '/logs')
api.add_resource(QueryLogs, '/logs/query')

if __name__ == '__main__':
	app.run()