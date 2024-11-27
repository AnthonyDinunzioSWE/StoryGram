from flask import request, redirect, url_for, render_template, session, flash
import os
from werkzeug.utils import secure_filename
from datetime import datetime

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os


# Flask INIT
app = Flask(__name__,
            template_folder=os.path.join(os.path.dirname(__file__), "../frontend/templates"),
            static_folder=os.path.join(os.path.dirname(__file__), "../frontend/static")
            )

# App Configurations
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///storygram.db"
app.config["DATABASE_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "randomKey"

# Database INIT
db = SQLAlchemy(app)

migrate = Migrate(app, db)



ALLOWED_EXTENSIONS = ["png", "jpg"]
UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# DATABASE MODELS

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
    liked_by_users = db.relationship(
    'User',
    secondary='likes',
    back_populates='liked_posts'
)
    disliked_by_users = db.relationship(
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


# APP ROUTES
@app.route("/")
def home():
    if "user_id" not in session:
        return redirect(url_for("login"))

    userid = session['user_id']
    posts = Post.query.all()
    
    user = User.query.get(userid)

    return render_template("index.html", posts=posts, user=user)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()

        if user and user.password == password:
            session["user_id"] = user.id
            session["username"] = user.username
            flash("Login successful!", "success")
            return redirect(url_for("profile"))
        else:
            flash("Invalid email or password.", "danger")
            return redirect(url_for("login"))


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html")
    
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        # Check if the email is already registered
        if User.query.filter_by(email=email).first():
            flash("Email is already registered.", "danger")
            return redirect(url_for("signup"))

        # Create a new user
        user = User(username=username, email=email, password=password)
        db.session.add(user)
        db.session.commit()

        flash("Signup successful! Please log in.", "success")
        return redirect(url_for("login"))


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("home"))

@app.route("/profile", methods=["GET", "POST"])
def profile():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    user = User.query.get(user_id)
    if not user:
        return "User not found", 404

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    like_counter = 0
    for post in user.posts:
        for like in post.likes:
            like_counter += 1
        
        post.like_counter = like_counter

    dislike_counter = 0
    for post in user.posts:
        for dislike in post.dislikes:
            dislike_counter += 1
            
        post.dislike_counter = dislike_counter

    # Handle POST request to create a new post
    if request.method == "POST":
        title = request.form.get("title")
        content = request.form.get("content")
        interests = request.form.getlist("interests")

        # Create new post
        new_post = Post(title=title, content=content, author=user)
        db.session.add(new_post)
        db.session.commit()

        # Add interests to the post
        for interest_id in interests:
            interest = Interest.query.get(interest_id)
            if interest:
                new_post.applied_interests.append(interest)

        db.session.commit()

        flash("Post created successfully!", "success")
        return redirect(url_for("profile"))

    return render_template("profile.html", user=user, current_time=current_time)


@app.route("/editProfile", methods=["GET", "POST"])
def edit_profile():
    user_id = session["user_id"]
    user = User.query.get(user_id)

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        bio = request.form.get("bio")
        profile_image = request.files.get("profile_image")

        if username != user.username and username != "":
            user.username = username

        if password != user.password and password != "":
            user.password = password

        if bio != user.bio and bio != "":
            user.bio = bio

        if profile_image and allowed_file(profile_image.filename):
            filename = secure_filename(profile_image.filename)
            profile_image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'profile_images', filename)
            profile_image.save(profile_image_path)
            user.profile_image = str(filename)
            db.session.commit()

        db.session.commit()

        flash("Profile updated successfully!", "success")
        return redirect(url_for("profile"))
    
    return render_template("edit_profile.html", user=user)


@app.route("/like_post/<int:post_id>", methods=["POST"])
def like_post(post_id):
    if "user_id" not in session:
        flash("Please log in to like a post.", "warning")
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])
    post = Post.query.get(post_id)

    if not post:
        flash("Post not found.", "danger")
        return redirect(url_for("home"))

    # Check if the user already liked the post
    if user in post.likes:
        # If already liked, remove the like
        post.likes.remove(user)
        flash("Like removed.", "info")
    else:
        # If not liked, add the like
        # Ensure the user has not disliked the post
        if user in post.dislikes:
            post.dislikes.remove(user)
        post.likes.append(user)
        flash("You liked the post.", "success")

    db.session.commit()
    return redirect(url_for("home"))


@app.route("/dislike_post/<int:post_id>", methods=["POST"])
def dislike_post(post_id):
    if "user_id" not in session:
        flash("Please log in to dislike a post.", "warning")
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])
    post = Post.query.get(post_id)

    if not post:
        flash("Post not found.", "danger")
        return redirect(url_for("home"))

    # Check if the user already disliked the post
    if user in post.dislikes:
        # If already disliked, remove the dislike
        post.dislikes.remove(user)
        flash("Dislike removed.", "info")
    else:
        # If not disliked, add the dislike
        # Ensure the user has not liked the post
        if user in post.likes:
            post.likes.remove(user)
        post.dislikes.append(user)
        flash("You disliked the post.", "success")

    db.session.commit()
    return redirect(url_for("home"))

@app.route("/add_comment/<int:post_id>", methods=["GET", "POST"])
def add_comment(post_id):
    post = Post.query.get(post_id)
    if request.method == "POST":
        content = request.form.get("content")
        # Create new comment logic here (assuming you have a Comment model)
        comment = Comment(content=content, post=post, author=User.query.get(session['user_id']))
        db.session.add(comment)
        db.session.commit()
        flash("Comment added!", "success")
        return redirect(url_for("home"))
    return render_template("add_comment.html", post=post)

@app.route("/thread_post/<int:post_id>", methods=["GET", "POST"])
def thread_post(post_id):
    post = Post.query.get(post_id)
    if request.method == "POST":
        title = request.form.get("title")
        content = request.form.get("content")
        # Create new thread logic here (assuming you have a Thread model)
        thread = Thread(title=title, content=content, post=post, author=User.query.get(session['user_id']))
        db.session.add(thread)
        db.session.commit()
        flash("Thread created!", "success")
        return redirect(url_for("home"))
    return render_template("create_thread.html", post=post)


@app.route("/delete_post/<int:post_id>", methods=["POST"])
def delete_post(post_id):
    post = Post.query.get(post_id)
    if post:
        db.session.delete(post)
        db.session.commit()
        flash("Deleted Post Successfully!")
    else:
        flash("Error Deleting Post: Could Not Find Post ID")
    
    return redirect(url_for("profile"))


@app.route("/search", methods=["GET", "POST"])
def search():
    # Ensure the user is logged in
    if "user_id" not in session:
        return redirect(url_for("login"))

    # Get the logged-in user
    userid = session["user_id"]
    user = User.query.get(userid)

    if request.method == "POST":
        # Get the search term from the form
        search_term = request.form.get("username")
        if search_term:
            # Perform a case-insensitive search for the username
            search_results = User.query.filter(
                User.username.ilike(f"%{search_term}%")
            ).all()
        else:
            search_results = []
        return render_template("search.html", user=user, search_results=search_results)

    # GET request - render search page
    return render_template("search.html", user=user)


@app.route("/view_profile/<int:user_id>", methods=["GET", "POST"])
def view_profile(user_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    # Get the logged-in user and the user whose profile is being viewed
    current_user = User.query.get(session["user_id"])
    user = User.query.get(user_id)
    if not user:
        return "User not found", 404

    # Check if the current user is following the viewed user
    is_following = current_user in user.followers

    # Handle follow/unfollow logic
    if request.method == "POST":
        if current_user in user.followers:
            user.followers.remove(current_user)  # Unfollow
            flash("You have unfollowed this user.", "info")
        else:
            user.followers.append(current_user)  # Follow
            flash("You are now following this user.", "success")

        db.session.commit()
        return redirect(url_for("view_profile", user_id=user_id))  # Reload the page

    # Posts Section
    posts = Post.query.filter_by(author_id=user_id).all()

    return render_template("view_profile.html", user=user, current_user=current_user, is_following=is_following, posts=posts)  


@app.route("/messages")
def messages():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    user = User.query.get(user_id)
    
    # Fetch conversations for the logged-in user
    conversations = Conversation.query.join(ConversationParticipants).filter(ConversationParticipants.user_id == user_id).all()
    
    return render_template("messages.html", user=user, conversations=conversations)

@app.route("/new_message", methods=["GET", "POST"])
def new_message():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    user = User.query.get(user_id)

    if request.method == "POST":
        recipient_id = request.form.get("recipient_id")
        content = request.form.get("content")
        
        # Create a new conversation or fetch an existing one
        recipient = User.query.get(recipient_id)
        if not recipient:
            flash("User not found.", "danger")
            return redirect(url_for("messages"))
        
        # Create conversation
        conversation = Conversation(participants=[user, recipient])
        db.session.add(conversation)
        db.session.commit()
        
        # Send the first message
        message = Message(content=content, sender_id=user.id, conversation_id=conversation.id)
        db.session.add(message)
        db.session.commit()

        flash("Message sent!", "success")
        return redirect(url_for("messages"))

    # Fetch all users except the logged-in user for the "New Message" form
    users = User.query.filter(User.id != user_id).all()
    return render_template("new_message.html", user=user, users=users)

@app.route("/conversation/<int:conversation_id>")
def conversation(conversation_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    user = User.query.get(user_id)
    conversation = Conversation.query.get(conversation_id)

    if not conversation or user not in conversation.participants:
        flash("Conversation not found.", "danger")
        return redirect(url_for("messages"))

    # Mark all messages as read
    for message in conversation.messages:
        if message.sender_id != user.id:
            message.is_read = True
    db.session.commit()

    return render_template("conversation.html", user=user, conversation=conversation)

@app.route("/send_message/<int:conversation_id>", methods=["POST"])
def send_message(conversation_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    user = User.query.get(user_id)
    conversation = Conversation.query.get(conversation_id)

    if not conversation or user not in conversation.participants:
        flash("Conversation not found.", "danger")
        return redirect(url_for("messages"))

    content = request.form.get("content")
    message = Message(content=content, sender_id=user.id, conversation_id=conversation.id)
    db.session.add(message)
    db.session.commit()

    flash("Message sent!", "success")
    return redirect(url_for("conversation", conversation_id=conversation_id))


@app.route("/create_conversation", methods=["GET", "POST"])
def create_conversation():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    user = User.query.get(user_id)

    # Fetch followers and following
    followers = user.followers
    following = user.following
    seen_users = []
    
    # Avoid duplicates in participants list (followers + following)
    for follower in followers:
        if follower not in seen_users:
            seen_users.append(follower)

    for act in following:
        if act not in seen_users:
            seen_users.append(act)

    if request.method == "POST":
        # Get selected participants from the form
        selected_participants_ids = request.form.getlist("participants")
        
        # Include the user in the conversation by default
        selected_participants_ids.append(str(user.id))

        # Query users for the selected participant IDs
        selected_participants = User.query.filter(User.id.in_(selected_participants_ids)).all()

        # Create the conversation with the selected participants
        conversation = Conversation(participants=[user] + selected_participants)
        db.session.add(conversation)
        db.session.commit()

        # Add participants to ConversationParticipants table
        for participant in selected_participants:
            conversation_participant = ConversationParticipants(conversation_id=conversation.id, user_id=participant.id)
            db.session.add(conversation_participant)

        db.session.commit()

        flash("Conversation created successfully!", "success")
        return redirect(url_for("messages"))

    return render_template("create_conversation.html", user=user, participants=seen_users)


@app.route("/select_participants", methods=["GET", "POST"])
def select_participants():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    user = User.query.get(user_id)

    # Get followers and following
    followers = user.followers
    following = user.following
    seen_users = []
     # Avoid duplicates in participants list (followers + following)
    for follower in followers:
        if follower not in seen_users:
            seen_users.append(follower)

    for act in following:
        if act not in seen_users:
            seen_users.append(act)
    

    if request.method == "POST":
        # Get selected participants from the form
        selected_participants_ids = request.form.getlist("participants")
        selected_participants = User.query.filter(User.id.in_(selected_participants_ids)).all()

        # Create the conversation
        conversation = Conversation(participants=[user] + selected_participants)
        db.session.add(conversation)
        db.session.commit()

        # Add participants to ConversationParticipants table
        for participant in selected_participants:
            conversation_participant = ConversationParticipants(conversation_id=conversation.id, user_id=participant.id)
            db.session.add(conversation_participant)

        db.session.commit()

        flash("Conversation created successfully!", "success")
        return redirect(url_for("messages"))

    return render_template("select_participants.html", user=user, participants=seen_users)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)