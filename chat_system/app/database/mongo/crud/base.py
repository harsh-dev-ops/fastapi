from uuid import uuid4
from beanie import Document
from typing import List
from bson import ObjectId
from datetime import datetime

from fastapi import HTTPException
from pydantic import UUID4
from app.database.mongo.base import BaseDocument


class CrudMixins:
    def __init__(self, model: Document):
        self.model = model

    async def missing_obj(self,obj: Document) -> None:
        if obj is None:
            raise HTTPException(404, "Object not found")
        return None
    
    async def update_obj(self, obj: BaseDocument, data: dict) -> Document:
        await self.missing_obj(obj)
        for key, value in data.items():
            setattr(obj, key, value)
        await obj.save()
        return obj
    
    async def delete_obj(self, obj: Document):
        await self.missing_obj(obj)
        await obj.delete()

    async def pagination(self, query, page: int =1, page_size: int = 50):
        skip = page_size * (page - 1)
        limit = page_size
        return await query.skip(skip).limit(limit).to_list()


class BaseCrud(CrudMixins):
    def __init__(self, model: Document):
        super().__init__(model=model)

    async def get_all(self) -> List[Document]:
        return await self.model.find_all().sort("-created_at").to_list()
    
    async def get(self, _id: str, fetch_links: bool = True) -> Document:
        return await self.model.get(str(_id), fetch_links=fetch_links)

    async def get_by_uid(self, uid: str) -> Document:
        obj = await self.model.find(self.model.uid == uid).first_or_none()
        await self.missing_obj(obj)
        return obj

    async def create(self, data: dict) -> Document:
        obj = self.model(**data)
        return await obj.insert()

    async def update(self, id: str, data: dict) -> Document:
        obj = await self.get(id, fetch_links=False)
        return await self.update_obj(obj, data)

    async def update_by_uid(self, uid: UUID4, data:dict) -> Document:
        obj = await self.get_by_uid(uid)
        return await self.update_obj(obj, data)
    
    async def delete(self, id: str) -> Document:
        obj = await self.model.get(id, fetch_links=False)
        await self.delete_obj(obj)

    async def delete_by_uid(self, uid: UUID4):
        obj = await self.get_by_uid(uid)
        await self.delete_obj(obj)
    
    

