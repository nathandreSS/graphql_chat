from ariadne import ObjectType, convert_kwargs_to_snake_case
from secrets import token_urlsafe
from mongoengine.queryset.visitor import Q
from werkzeug.security import generate_password_hash, check_password_hash

from .store import users, messages, groups, queues
from .models import Users, Tokens, to_dict
from api import app

mutation = ObjectType("Mutation")


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

