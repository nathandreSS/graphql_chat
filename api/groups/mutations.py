from ariadne.objects import MutationType
from ariadne import convert_kwargs_to_snake_case
from mongoengine.queryset.visitor import Q

from api.models import Groups, to_dict
from api import app
from api.users.utils import user_exists

groups_mutation = MutationType()
@groups_mutation.field("createGroup")
@convert_kwargs_to_snake_case
def resolve_create_group(obj, info, name, users_id):
    try:
        users_id = list(set(users_id))
        inexistent_users = []
        for user_id in users_id:
            if not user_exists(user_id):
                inexistent_users.append(user_id)

        users_id = list(set(users_id)-set(inexistent_users))
        group = Groups(name=name, users=users_id).save()
        return {
            "group": to_dict(Groups.objects.get(_id=group._id)),
            "success": True
        }
    except Exception as error:
        return {
            "success": False,
            "errors": [str(error)]
        }

@groups_mutation.field("addUsersToGroup")
@convert_kwargs_to_snake_case
def resolve_add_users_to_group(obj, info, group_id, users_id):
    try:
        group = Groups.objects.get(group_id)
        group.users = set(group.users + users_id)
        group.save()

        return {
            "group": group,
            "success": True
        } 
    except Exception as error:
        type(error)
        return {
            "success": False,
            "errors": [str(error)]
        }