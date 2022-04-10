from flask import Flask, request, jsonify
import datetime as dt
from flask_restful import Resource, Api, reqparse, abort
import pandas as pd
import cons


def check_api_key(api_key):
    if api_key != cons.api_key_static:
        abort(401, message="unauthorized: invalid API key")