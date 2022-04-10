from flask_restful import abort
import cons


def check_api_key(api_key):
    if api_key != cons.api_key_static:
        abort(401, message="unauthorized: invalid API key")