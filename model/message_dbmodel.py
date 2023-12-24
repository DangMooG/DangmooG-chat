from sqlalchemy import Column, Integer, text, ForeignKey, String, Null, VARCHAR, CHAR, TEXT
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import relationship
from sqlalchemy.types import TIMESTAMP
import uuid

from core.db import Base


class Room(Base):
    __tablename__ = "room"
    room_id = Column(String, primary_key=True, default=str(uuid.uuid4()), unique=True, nullable=False)
    seller_id = Column(Integer, ForeignKey("account.account_id"), nullable=False)
    rooms_of_seller = relationship("Account", foreign_keys=[seller_id], backref="chat_rooms_seller")
    buyer_id = Column(Integer, ForeignKey("account.account_id"), nullable=False)
    rooms_of_buyer = relationship("Account", foreign_keys=[buyer_id], backref="chat_rooms_buyer")
    status = Column(TINYINT, default=Null, comment="Null: 모두 읽기 가능, user_id: 해당 user_id 만 읽을 수 있음, -1: 아무도 못읽음")
    create_time = Column(TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    update_time = Column(
        TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")
    )
    mysql_engine = "InnoDB"


class Message(Base):
    __tablename__ = "message"
    message_id = Column(Integer, nullable=False, autoincrement=True, primary_key=True)
    room_id = Column(String, ForeignKey("room.room_id"), nullable=False)
    is_from_buyer = Column(TINYINT, nullable=False)
    content = Column(String, nullable=False)
    read = Column(TINYINT, default=0)
    create_time = Column(TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    mysql_engine = "InnoDB"


class Account(Base):
    __tablename__ = "account"
    account_id = Column(Integer, primary_key=True)
    username = Column(VARCHAR(30), unique=True, nullable=False)
    password = Column(CHAR(60), nullable=False)
    email = Column(VARCHAR(255), unique=True, nullable=False)
    profile_url = Column(VARCHAR(2000))
    available = Column(TINYINT, nullable=False)
    jail_until = Column(TIMESTAMP)
    refresh_token = Column(TEXT)
    create_time = Column(TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    update_time = Column(
        TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")
    )

    mysql_engine = "InnoDB"