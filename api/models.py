from datetime import datetime, timedelta, timezone
from enum import unique
from flask_mongoengine import Document
from mongoengine.fields import DateTimeField, EmailField, ListField, ReferenceField, StringField, UUIDField
from secrets import token_urlsafe
from uuid import uuid4

from api import db

def to_dict(query):
    object = query.to_mongo()
    object['id'] = object['_id']
    object.pop('_id')
    return object


class Users(db.Document):
    _id = UUIDField(default=uuid4())
    nickname = StringField(min_length=4, max_length=18, unique=True)
    email = EmailField(unique=True)
    password = StringField(min_length=8)
    last_login = DateTimeField(null=True)
    created_at = DateTimeField(default=datetime.now())

    def __str__(self):
        return self.nickname

FIVE_MINUTES_FROM_NOW = datetime.now() + timedelta(minutes=5)
class Tokens(db.Document):
    token = StringField(default=token_urlsafe(8), unique=True)
    exp = DateTimeField(default=FIVE_MINUTES_FROM_NOW)
    user_id = ReferenceField(Users)

class Groups(Document):
    _id = UUIDField(default=uuid4())
    name = StringField(max_length=30)
    users = ListField(ReferenceField(Users))
    administrators = ListField(ReferenceField(Users))
    created_at = DateTimeField(default=datetime.now())

    def __str__(self):
        return self.name


class Messages(Document):
    _id = UUIDField(default=uuid4())
    sender = ReferenceField(Users)
    group = ReferenceField(Groups, null=True)
    recipient = ReferenceField(Users, null=True)
    content = StringField()
    read_by = ListField(ReferenceField(Users))
    delivered_to = ListField(ReferenceField(Users))
    sended_at = DateTimeField(default=datetime.now())

    def __str__(self):
        return self._id