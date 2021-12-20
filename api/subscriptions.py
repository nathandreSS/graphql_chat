import asyncio
from ariadne import convert_kwargs_to_snake_case, SubscriptionType

from .store import queues, groups

subscription = SubscriptionType()


@subscription.source("messages")
@convert_kwargs_to_snake_case
async def messages_source(obj, info, user_id):
    queue = asyncio.Queue()
    queues.append(queue)
    try:
        while True:
            print('listen')
            message = await queue.get()
            queue.task_done()
            if message.get('recipient_id') == user_id:
                yield message
            if message.get("group_id"):
                if user_id in groups[message.get('group_id')]['users_ids']:
                    yield message
    except asyncio.CancelledError:
        queues.remove(queue)
        raise


@subscription.field("messages")
@convert_kwargs_to_snake_case
async def messages_resolver(message, info, user_id):
    return message