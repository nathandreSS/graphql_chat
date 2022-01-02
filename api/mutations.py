import json
import jwt
import re
import time

from ariadne import ObjectType, convert_kwargs_to_snake_case
from cryptography.fernet import Fernet
from datetime import datetime, timezone,timedelta
from flask_mail import Mail, Message
from mongoengine.errors import NotUniqueError, ValidationError
from secrets import token_urlsafe
from mongoengine.queryset.visitor import Q
from werkzeug.security import generate_password_hash, check_password_hash

from .store import users, messages, groups, queues
from .models import Users, Tokens, to_dict
from api import app

mutation = ObjectType("Mutation")

def handle_unique_error_message(keys=[], error=''):
    for key in keys:
        if key in error:
            return  f"{key} already registered!"

def handle_validation_error_message(keys=[], error=''):
    for key in keys:
        if key in error:
            return  f"{key} is not valid!"


@mutation.field("login")
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

def verify_password_strength(password):
    return  re.match(re.compile('^(?=.*[A-Z].*[A-Z])' # At least 2 uppercase
                                '(?=.*[!@#$&*])' # At least 1 special character
                                '(?=.*[0-9].*[0-9])' # At least 2 digits
                                '(?=.*[a-z].*[a-z].*[a-z])' # At least 3 lowercase
                                '.{8,}$'), password)

@mutation.field("register")
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

def validate_email_token(token, user_id):
    token = Tokens.objects.filter(token=token).first()

    if not token or token.user_id != user_id:    
        return {"is_valid": False, "error": "Invalid token!"}

    if datetime.timestamp(datetime.now()) > datetime.timestamp(token.exp) :
        return {"is_valid": False, "error": "Expired token!"}
    
    return {"is_valid": True}

@mutation.field("sendTokenToEmail")
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

@mutation.field("createMessage")
@convert_kwargs_to_snake_case
async def resolve_create_message(obj, info, content, sender_id, recipient_id):
    try:
        message = {
            "content": content,
            "sender_id": sender_id,
            "recipient_id": recipient_id,
        }
        messages.append(message)
        for queue in queues:
            await queue.put(message)
        return {
            "success": True,
            "message": message
        }
    except Exception as error:
        return {
            "success": False,
            "errors": [str(error)]
        }

@mutation.field("createGroupMessage")
@convert_kwargs_to_snake_case
async def resolve_create_group_message(obj, info, content, sender_id, group_id):
    try:
        if not groups.get(group_id):
            return {
                "success": False,
                "errors": ["Group not found."]
            }
        if not sender_id in groups[group_id]["users_ids"]:
            return {
                "success": False,
                "errors": ["Users not in group."]
            }
        message = {
            "content": content,
            "sender_id": sender_id,
            "group_id": group_id
        }
        messages.append(message)
        for queue in queues:
            await queue.put(message)
        return {
            "success": True,
            "message": message
        }
    except Exception as error:
        return {
            "success": False,
            "errors": [str(error)]
        }

@mutation.field("createGroup")
@convert_kwargs_to_snake_case
async def resolve_create_group(obj, info, name, users_ids):
    try:
        group = {
            "group_id": f'{len(groups) + 1}',
            "name": name,
            "users_ids": set(users_ids)
        }
        groups[group["group_id"]] = group
        return {
            "group": group,
            "success": True
        }
    except Exception as error:
        return {
            "success": False,
            "errors": [str(error)]
        }

@mutation.field("addUsersToGroup")
@convert_kwargs_to_snake_case
async def resolve_add_users_to_group(obj, info, group_id, users_ids):
    try:
        group = groups[group_id]
        group["users_ids"].update(set(users_ids))
        groups[group_id] = group
        return {
            "group": group,
            "success": True
        } 
    except KeyError as error:
        return {
            "success": False,
            "errors": ["Group not found"]
        }
    except Exception as error:
        return {
            "success": False,
            "errors": [str(error)]
        }