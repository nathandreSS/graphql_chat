import re

from datetime import datetime
from mongoengine.queryset.visitor import Q

from api.models import Tokens, Users

def user_exists(user_id):
    user = Users.objects.filter(_id=user_id).first()
    if user:
        return True
    return False


def validate_email_token(token, user_id):
    token = Tokens.objects.filter(token=token).first()

    if not token or token.user_id != user_id:    
        return {"is_valid": False, "error": "Invalid token!"}

    if datetime.timestamp(datetime.now()) > datetime.timestamp(token.exp) :
        return {"is_valid": False, "error": "Expired token!"}
    
    return {"is_valid": True}


def verify_password_strength(password):
    return  re.match(re.compile('^(?=.*[A-Z].*[A-Z])' # At least 2 uppercase
                                '(?=.*[!@#$&*])' # At least 1 special character
                                '(?=.*[0-9].*[0-9])' # At least 2 digits
                                '(?=.*[a-z].*[a-z].*[a-z])' # At least 3 lowercase
                                '.{8,}$'), password)