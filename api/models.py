from flask_mongoengine import Document
from mongoengine.fields import DateTimeField, EmailField, ListField, ReferenceField, StringField, UUIDField
from datetime import datetime
from uuid import uuid4
from api import db

def to_dict(query):
    object = query.to_mongo()
    object['id'] = object['_id']
    object.pop('_id')
    return object
class User(db.Document):
    _id = UUIDField(default=uuid4())
    nickname = StringField(min_length=4, max_length=18, unique=True)
    email = EmailField(unique=True)
    token = StringField()
    last_login = DateTimeField(null=True)
    created_at = DateTimeField(default=datetime.now())

    def __str__(self):
        return self.nickname


class Group(Document):
    _id = UUIDField(default=uuid4())
    name = StringField(max_length=30)
    users = ListField(ReferenceField(User))
    administrators = ListField(ReferenceField(User))
    created_at = DateTimeField(default=datetime.now())

    def __str__(self):
        return self.name


class Message(Document):
    _id = UUIDField(default=uuid4())
    sender = ReferenceField(User)
    group = ReferenceField(Group, null=True)
    recipient = ReferenceField(User, null=True)
    content = StringField()
    read_by = ListField(ReferenceField(User))
    delivered_to = ListField(ReferenceField(User))
    sended_at = DateTimeField(default=datetime.now())

    def __str__(self):
        return self._id