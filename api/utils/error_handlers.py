def handle_unique_error_message(keys=[], error=''):
    for key in keys:
        if key in error:
            return  f"{key} already registered!"

def handle_validation_error_message(keys=[], error=''):
    for key in keys:
        if key in error:
            return  f"{key} is not valid!"