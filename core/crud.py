from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from typing import Union


class CRUD:
    def __init__(self, session: Session) -> None:
        self.session = session
        # self.query = self.session.query(table)

    def get_list(self, table: BaseModel):
        return self.session.query(table).all()

    def get_record(self, table: BaseModel, cond={}):
        filters = []
        for table_id, id in cond.items():
            filters.append(getattr(table, table_id) == id)
        return self.session.query(table).filter(*filters).first()

    def create_record(self, table: BaseModel, req: BaseModel):
        db_record = table(**req.dict())
        self.session.add(db_record)
        self.session.commit()
        self.session.refresh(db_record)
        return db_record

    def update_record(self, db_record: BaseModel, req: Union[BaseModel, dict]):
        if isinstance(req, BaseModel):
            req = req.dict()
        for key, value in req.items():
            setattr(db_record, key, value)
        self.session.commit()

        return db_record

    def patch_record(self, db_record: BaseModel, req: Union[BaseModel, dict]):
        if isinstance(req, BaseModel):
            req = req.dict()
        for key, value in req.items():
            if value:
                setattr(db_record, key, value)
            if value == 0:
                setattr(db_record, key, value)
        self.session.commit()

        return db_record


    def search_record(self, table: BaseModel, req: Union[BaseModel, dict]):
        if isinstance(req, BaseModel):
            req = req.dict()
        filters = []
        for key, value in req.items():
            if value == 0 or value:
                if isinstance(value, (int, float)):
                    filters.append(getattr(table, key) == value)
                elif isinstance(value, str):
                    filters.append(getattr(table, key).contains(value))
                elif isinstance(value, list):
                    filters.append(func.json_contains(getattr(table, key), str(value)) == 1)

        result = self.session.query(table).filter(*filters).all()
        return result
