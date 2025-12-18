from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from .db import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    avatar_url = Column(String(255))
    fon_url = Column(String(255))

    messages_sent = relationship("Message", back_populates="sender")
    chats = relationship("ChatMember", back_populates="user")
    posts = relationship("Post", back_populates="author")

    friends = relationship(
        "Friend",
        foreign_keys="[Friend.user_id]",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    friend_of = relationship(
        "Friend",
        foreign_keys="[Friend.friend_id]",
        back_populates="friend",
        cascade="all, delete-orphan"
    )

    comments = relationship("Comment", back_populates="author", cascade="all, delete-orphan")
    settings = relationship("Settings", back_populates="user", uselist=False, cascade="all, delete-orphan")


class Chat(Base):
    __tablename__ = 'chats'

    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    is_group = Column(Boolean, default=False)

    members = relationship("ChatMember", back_populates="chat", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="chat", cascade="save-update")


class ChatMember(Base):
    __tablename__ = 'chat_members'

    chat_id = Column(Integer, ForeignKey('chats.id'), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    joined_at = Column(DateTime, default=datetime.utcnow)

    chat = relationship("Chat", back_populates="members")
    user = relationship("User", back_populates="chats")


class Message(Base):
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, ForeignKey('chats.id'), nullable=False)
    sender_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    content = Column(Text)
    attachment_url = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    is_read = Column(Boolean, default=False)

    chat = relationship("Chat", back_populates="messages")
    sender = relationship("User", back_populates="messages_sent")


class Post(Base):
    __tablename__ = 'posts'

    id = Column(Integer, primary_key=True)
    author_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    title = Column(String(255))
    content = Column(Text, nullable=False)
    image_url = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    is_published = Column(Boolean, default=True)

    author = relationship("User", back_populates="posts", lazy="selectin")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")
    likes = relationship("Like", back_populates="post", cascade="all, delete-orphan")


class Comment(Base):
    __tablename__ = 'comments'

    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey('posts.id'), nullable=False)
    author_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    post = relationship("Post", back_populates="comments")
    author = relationship("User")


class Image(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, unique=True, index=True)
    filepath = Column(String)
    content_type = Column(String)


class Like(Base):
    __tablename__ = "likes"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey('posts.id'), nullable=False)
    author_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    post = relationship("Post", back_populates="likes")
    author = relationship("User")


class Friend(Base):
    __tablename__ = "friends"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    friend_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    status = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    # updated_at = Column(DateTime, default=datetime.utcnow)

    user = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="friends"
    )
    friend = relationship(
        "User",
        foreign_keys=[friend_id],
        back_populates="friend_of"
    )


class Settings(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, unique=True)
    notifications_enabled = Column(Boolean, default=True)
    theme = Column(String, default="light")

    user = relationship("User", back_populates="settings")
