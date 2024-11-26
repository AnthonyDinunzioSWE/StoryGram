from config import db
from datetime import datetime

# User Table
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    profile_picture = db.Column(db.String(255), nullable=True)

    posts = db.relationship('Post', backref='author', lazy=True)
    threads = db.relationship('Thread', backref='author', lazy=True)
    followers = db.relationship(
        'User', 
        secondary='followers', 
        primaryjoin='User.id==followers.c.following_id',
        secondaryjoin='User.id==followers.c.follower_id',
        backref='following'
    )
    liked_posts = db.relationship(
        'Post',
        secondary='likes',
        back_populates='liked_by_users'
    )
    conversations = db.relationship(
        'Conversation',
        secondary='conversation_users',
        back_populates='users'
    )

# Post Table
class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(255), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    threads = db.relationship('Thread', backref='parent_post', lazy=True)
    comments = db.relationship('Comment', backref='post', lazy=True)
    likes = db.relationship(
        'User',
        secondary='likes',
        back_populates='liked_posts'
    )
    dislikes = db.relationship(
        'User',
        secondary='dislikes',
        back_populates='disliked_posts'
    )

# Thread Table
class Thread(db.Model):
    __tablename__ = 'threads'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(255), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=True)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    comments = db.relationship('Comment', backref='thread', lazy=True)
    likes = db.relationship(
        'User',
        secondary='thread_likes',
        back_populates='liked_threads'
    )
    dislikes = db.relationship(
        'User',
        secondary='thread_dislikes',
        back_populates='disliked_threads'
    )

# Comment Table
class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=True)
    thread_id = db.Column(db.Integer, db.ForeignKey('threads.id'), nullable=True)

# Conversation Table
class Conversation(db.Model):
    __tablename__ = 'conversations'
    id = db.Column(db.Integer, primary_key=True)
    messages = db.relationship('Message', backref='conversation', lazy=True)
    users = db.relationship(
        'User',
        secondary='conversation_users',
        back_populates='conversations'
    )

# Message Table
class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=False)

# Association Tables
followers = db.Table(
    'followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('following_id', db.Integer, db.ForeignKey('users.id'), primary_key=True)
)

likes = db.Table(
    'likes',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('post_id', db.Integer, db.ForeignKey('posts.id'), primary_key=True)
)

dislikes = db.Table(
    'dislikes',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('post_id', db.Integer, db.ForeignKey('posts.id'), primary_key=True)
)

thread_likes = db.Table(
    'thread_likes',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('thread_id', db.Integer, db.ForeignKey('threads.id'), primary_key=True)
)

thread_dislikes = db.Table(
    'thread_dislikes',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('thread_id', db.Integer, db.ForeignKey('threads.id'), primary_key=True)
)

conversation_users = db.Table(
    'conversation_users',
    db.Column('conversation_id', db.Integer, db.ForeignKey('conversations.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True)
)
