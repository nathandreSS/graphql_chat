import jwt

import time

from ariadne import ObjectType, convert_kwargs_to_snake_case
from datetime import datetime, timezone,timedelta
from flask_mail import Mail, Message
from mongoengine.errors import NotUniqueError, ValidationError
from secrets import token_urlsafe
from mongoengine.queryset.visitor import Q
from werkzeug.security import generate_password_hash, check_password_hash

from api import app
from api.models import Users, Tokens, to_dict
from api.users.utils import validate_email_token, verify_password_strength
from api.utils.error_handlers import handle_unique_error_message, handle_validation_error_message

auth_mutation = ObjectType("Mutation")
@auth_mutation.field("register")
@convert_kwargs_to_snake_case
def resolve_register(obj, info, email, password, nickname):
    try:
        if not verify_password_strength(password):
            return {
                "success": False,
                "errors": ["Weak password!", 
                            "A strong password must have at least 2 uppercase letters,\
                            3 lowercase letters, 1 special character and 2 digits."]
            }
        hashed_password = generate_password_hash(password)
        Users(email=email, nickname=nickname, password=hashed_password).save()
        user = to_dict(Users.objects.filter(email=email).first())

        return {
            "success": True,
            "user": user
        }
    except NotUniqueError as error:
        return {
            "success": False,
            "errors": [handle_unique_error_message(keys=['nickname', 'email'], error=str(error))]
        }
    except ValidationError as error:       
        return {
            "success": False,
            "errors": [handle_validation_error_message(keys=['nickname', 'email'], error=str(error))]
        }
    except Exception as error:
        return {
            "success": False,
            "errors": [str(error)]
        }

@auth_mutation.field("sendTokenToEmail")
@convert_kwargs_to_snake_case
def resolve_send_token_to_email(obj, info, email, password):
    user = Users.objects.get(email=email)

    if not user or not check_password_hash(user.password, password):
        return {
            "success": False,
            "errors": ["Wrong credentials!"]
        }
    
    msg = Message('Authentication Token', sender = app.config["MAIL_USERNAME"], recipients = [email])

    expired_tokens = Tokens.objects(Q(exp__lt=datetime.now(tz=timezone.utc)))
    expired_tokens.delete()

    while True:
        try:
            token = Tokens(token=token_urlsafe(8)).save()
            msg.body = token.token
            Mail(app).send(msg)
            
            return {
                "success": True,
            }
        except NotUniqueError:
            continue
        except Exception as error:
            return {
                "success": False,
                "errors": [str(error)]
            }


@auth_mutation.field("login")
@convert_kwargs_to_snake_case
def resolve_login(obj, info, email, password, token):
    user = Users.objects.get(email=email)

    if not user or not check_password_hash(user.password, password):
        return {
            "success": False,
            "errors": ["Wrong credentials!"]
        }
    
    token_validation = validate_email_token(token, user.id)
    if not token_validation['is_valid']:
        return {
            "success": False,
            "errors": [token_validation['error']]
        }
    
    tomorrow_as_unixtime = time.mktime((datetime.now(tz=timezone.utc) + timedelta(days=1)).timetuple())
    jwt_token = jwt.encode({"ext": tomorrow_as_unixtime, "user_id": user.id}, app.config["SECRET_KEY"])
    
    return {
        "success": True,
        "jwt_token": jwt_token
    }



