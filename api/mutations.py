from ariadne import ObjectType, convert_kwargs_to_snake_case
from mongoengine.errors import NotUniqueError, ValidationError
from secrets import token_urlsafe
from flask_mail import Mail, Message

from api import app
from .store import users, messages, groups, queues
from .models import User, to_dict
mutation = ObjectType("Mutation")

def handle_unique_error_message(keys=[], error=''):
    for key in keys:
        if key in error:
            return  f"{key} already registered!"

def handle_validation_error_message(keys=[], error=''):
    for key in keys:
        if key in error:
            return  f"{key} is not valid!"

@mutation.field("register")
@convert_kwargs_to_snake_case
async def resolve_create_user(obj, info, email, nickname):
    try:
        User(email=email, nickname=nickname).save()
        user = to_dict(User.objects.filter(email=email).first())
        return {
            "success": True,
            "user": user
        }
    # except NotUniqueError as error:
    #     return {
    #         "success": False,
    #         "errors": [handle_unique_error_message(keys=['nickname', 'email'], error=str(error))]
    #     }
    # except ValidationError as error:       
    #     return {
    #         "success": False,
    #         "errors": [handle_validation_error_message(keys=['nickname', 'email'], error=str(error))]
    #     }
    except Exception as error:
        return {
            "success": False,
            "errors": [str(error)]
        }


@mutation.field("sendTokenToEmail")
@convert_kwargs_to_snake_case
def resolve_send_token_to_email(obj, info, email):
    token = token_urlsafe(8)

    msg = Message('Authentication Token', sender = 'nathandreandre@gmail.com', recipients = [email])
    msg.body = token

    user = User.objects.get(email=email)
    user.token = token

    Mail(app).send(msg)
    
    return {
        "success": True,
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
                "errors": ["User not in group."]
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