import json


def get_json_status_response(status_code: str, message: str) -> str:
    response = {
        'status': status_code,
        'message': message
    }
    return json.dumps(response)
