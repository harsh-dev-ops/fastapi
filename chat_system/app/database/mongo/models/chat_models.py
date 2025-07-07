from beanie import Document
from datetime import datetime
from typing import List

class User(Document):
    username: str
    online: bool = False

    class Settings:
        name = "users"

class Message(Document):
    sender_id: str
    receiver_id: str 
    content: str
    timestamp: datetime = datetime.now()
    read_by: List[str] = [] 
    is_group: bool = False

    class Settings:
        name = "messages"

class Group(Document):
    name: str
    members: List[str]
    admin: str

    class Settings:
        name = "groups"