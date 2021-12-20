from ariadne import ObjectType, convert_kwargs_to_snake_case

from .store import users, messages, groups, queues

mutation = ObjectType("Mutation")


@mutation.field("createUser")
@convert_kwargs_to_snake_case
async def resolve_create_user(obj, info, username):
    try:
        if not users.get(username):
            user = {
                "user_id": len(users) + 1,
                "username": username
            }
            users[username] = user
            return {
                "success": True,
                "user": user
            }
        return {
            "success": False,
            "errors": ["Username is taken"]
        }

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