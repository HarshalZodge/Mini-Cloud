"""
Standard JSON API response helpers for MiniCloud.
Envelope:
  Success: { "success": true, "data": ... }
  Failure: { "success": false, "error": { "code": "...", "message": "...", "details": ... } }
"""
from flask import jsonify

def api_success(data=None, status_code: int = 200):
    payload = {
        "success": True,
        "data": data if data is not None else {}
    }
    return jsonify(payload), status_code

def api_error(code: str, message: str, status_code: int = 400, details=None):
    error_obj = {
        "code": code,
        "message": message
    }
    if details:
        error_obj["details"] = details
    payload = {
        "success": False,
        "error": error_obj
    }
    return jsonify(payload), status_code
