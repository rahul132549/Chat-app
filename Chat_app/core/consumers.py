import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import Message

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.user = self.scope['user']

        if not self.user.is_authenticated:
            await self.close()
            return

        self.other_user_id = self.scope['url_route']['kwargs']['user_id']

        # Create unique room name
        ids = sorted([self.user.id, int(self.other_user_id)])
        self.room_name = f"chat_{ids[0]}_{ids[1]}"

        await self.channel_layer.group_add(self.room_name, self.channel_name)
        await self.set_user_online(True)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'room_name'):
            await self.channel_layer.group_discard(self.room_name, self.channel_name)
            await self.set_user_online(False)

    async def receive(self, text_data):
        data = json.loads(text_data)
        m_type = data.get('type')

        # ------------------ SEND MESSAGE ------------------
        if m_type == 'message':
            content = data['content']
            message = await self.save_message(int(self.other_user_id), content)

            await self.channel_layer.group_send(
                self.room_name,
                {
                    'type': 'chat_message',
                    'message_id': message.id,
                    'sender_id': self.user.id,
                    'content': content,
                    'timestamp': str(message.timestamp),
                    'is_read': message.is_read,
                }
            )

        # ------------------ DELETE MESSAGE ------------------
        elif m_type == 'delete_message':
            msg_id = data.get('message_id')
            if await self.delete_message_db(msg_id):
                await self.channel_layer.group_send(
                    self.room_name,
                    {
                        'type': 'message_deleted',
                        'message_id': msg_id
                    }
                )

        # ------------------ EDIT MESSAGE ------------------
        elif m_type == 'edit_message':
            msg_id = data.get('message_id')
            new_content = data.get('content')
            if await self.edit_message_db(msg_id, new_content):
                await self.channel_layer.group_send(
                    self.room_name,
                    {
                        'type': 'message_edited',
                        'message_id': msg_id,
                        'content': new_content
                    }
                )

        # ------------------ READ RECEIPT ------------------
        elif m_type == 'read_receipt':
            await self.mark_messages_read()
            await self.channel_layer.group_send(
                self.room_name,
                {
                    'type': 'read_receipt_event',
                    'reader_id': self.user.id
                }
            )

        # ------------------ TYPING INDICATOR ------------------
        elif m_type == 'typing':
            await self.channel_layer.group_send(
                self.room_name,
                {
                    'type': 'typing_indicator',
                    'user_id': self.user.id,
                    'is_typing': data['is_typing']
                }
            )

    # ==========================================================
    # =============== BROADCAST HANDLERS =======================
    # ==========================================================

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message_id': event['message_id'],
            'sender_id': event['sender_id'],
            'content': event['content'],
            'timestamp': event['timestamp'],
            'is_read': event['is_read'],
        }))

    async def message_deleted(self, event):
        await self.send(text_data=json.dumps({
            'type': 'message_deleted',
            'message_id': event['message_id']
        }))

    async def message_edited(self, event):
        await self.send(text_data=json.dumps({
            'type': 'message_edited',
            'message_id': event['message_id'],
            'content': event['content']
        }))

    async def read_receipt_event(self, event):
        await self.send(text_data=json.dumps({
            'type': 'read_receipt',
            'reader_id': event['reader_id']
        }))

    async def typing_indicator(self, event):
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'user_id': event['user_id'],
            'is_typing': event['is_typing']
        }))

    # ==========================================================
    # =============== DATABASE OPERATIONS ======================
    # ==========================================================

    @database_sync_to_async
    def save_message(self, receiver_id, content):
        receiver = User.objects.get(id=receiver_id)
        return Message.objects.create(
            sender=self.user,
            receiver=receiver,
            content=content
        )

    @database_sync_to_async
    def delete_message_db(self, msg_id):
        return Message.objects.filter(
            id=msg_id,
            sender=self.user
        ).delete()[0] > 0

    @database_sync_to_async
    def edit_message_db(self, msg_id, content):
        return Message.objects.filter(
            id=msg_id,
            sender=self.user
        ).update(content=content) > 0

    @database_sync_to_async
    def set_user_online(self, status):
        User.objects.filter(id=self.user.id).update(is_online=status)

    @database_sync_to_async
    def mark_messages_read(self):
        Message.objects.filter(
            sender_id=self.other_user_id,
            receiver=self.user,
            is_read=False
        ).update(is_read=True)

