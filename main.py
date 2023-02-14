# **********---------- IMPORTS ----------**********
from flask import Flask, render_template, url_for, redirect, abort, flash
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
from flask_ckeditor import CKEditor
from datetime import date
from functools import wraps

from flask_wtf import CSRFProtect

import os


# **********---------- OWN IMPORTS ----------**********
from forms import RegisterForm, LoginForm, PostForm, CommentForm

# ------------------------------------------------------------------------------------------------------

# **********---------- APP ----------**********
app = Flask(__name__)
app.config["SECRET_KEY"] = "333333338888888800000000"
# app.config["SECRET_KEY"] = os.environ.get("APP_CONFIG_SECRET_KEY")
# print(os.getenv("APP_CONFIG_SECRET_KEY"))
# print(os.environ)
Bootstrap(app)
csrf = CSRFProtect(app)

# **********---------- DATABASE ----------**********
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
POSTGRES_DATABASE_EXTERNAL = 'postgresql://database_9nnd_user:noMrsdbrvjNZEEAe1Ga6KX7PwGNhHPw1@dpg-cfl0vhpmbjsn9efc6a10-a.frankfurt-postgres.render.com/database_9nnd'
POSTGRES_DATABASE_INTERNAL = 'postgresql://database_9nnd_user:noMrsdbrvjNZEEAe1Ga6KX7PwGNhHPw1@dpg-cfl0vhpmbjsn9efc6a10-a/database_9nnd'
app.config['SQLALCHEMY_DATABASE_URI'] = POSTGRES_DATABASE_EXTERNAL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Seems like this line is needed to create a new table:
app.app_context().push()


# **********---------- CK Editor ----------**********
ckeditor = CKEditor(app)
# Needs two lines of code when used:    {{ ckeditor.load() }}
#                                       {{ ckeditor.config(name='body') }}

# **********---------- LOGIN MANAGER ----------**********
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.id != 1 and current_user.id != 2:
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function

# ------------------------------------------------------------------------------------------------------


# **********---------- USER TABLE ----------**********
# | id | email | password | name |
class User(UserMixin, db.Model):
    __tablename__ = "users"

    # Primary Key:
    id = db.Column(db.Integer, primary_key=True)

    # Normal Tuples:
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))

    # One author - Many posts:
    posts = relationship("BlogPost", back_populates="author")

    # One author - Many comments:
    comments = relationship("Comment", back_populates="comment_author")


# **********---------- BLOGPOST TABLE ----------**********
# | id | title | subtitle | date | body | img_url | author_id: Foreign Key |
class BlogPost(db.Model):
    __tablename__ = "blog_posts"

    # Primary Key:
    id = db.Column(db.Integer, primary_key=True)

    # Normal Tuples:
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)

    # Foreign Key: (links each blog post to a specific author)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    # For every link between two tables, the following line is needed in both tables,
    # with a relationship that is "mirrored" (author-posts - posts-author).
    author = relationship("User", back_populates="posts")
    comments = relationship("Comment", back_populates="parent_post")


# **********---------- COMMENT TABLE ----------**********
# | id | text | post_id: Foreign Key | author_id: Foreign Key |
class Comment(db.Model):
    __tablename__ = "comments"

    # Primary Key:
    id = db.Column(db.Integer, primary_key=True)

    # Normal Tuples:
    text = db.Column(db.Text, nullable=False)
    date = db.Column(db.String(250), nullable=False)

    # Foreign Key: (links each comment to a specific blog post)
    post_id = db.Column(db.Integer, db.ForeignKey("blog_posts.id"))

    parent_post = relationship("BlogPost", back_populates="comments")

    # Foreign Key: (links each comment to a specific author)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    comment_author = relationship("User", back_populates="comments")

# db.create_all()

# ------------------------------------------------------------------------------------------------------


# **********---------- STANDARD ROUTES ----------**********
@app.route("/")
def home():
    user = None
    if current_user.is_authenticated:
        user = current_user
    posts = BlogPost.query.all()
    return render_template("index.html", posts=posts, user=user, logged_in=current_user.is_authenticated)


@app.route("/about")
def about():
    user = None
    if current_user.is_authenticated:
        user = current_user
    return render_template("about.html", title="Om sidan", user=user, logged_in=current_user.is_authenticated)


@app.route("/contact")
def contact():
    user = None
    if current_user.is_authenticated:
        user = current_user
    return render_template("contact.html", title="Kontakt", user=user, logged_in=current_user.is_authenticated)


# ------------------------------------------------------------------------------------------------------

# **********---------- USER ROUTES ----------**********

@app.route("/register", methods=["POST", "GET"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            flash("Emailadressen är redan registrerad. Försök att logga in.")
            return redirect(url_for("login"))
        password = form.password.data
        hashed_password = generate_password_hash(password, method="pbkdf2:sha256", salt_length=8)
        db.session.add(User(name=form.name.data, email=form.email.data, password=hashed_password))
        db.session.commit()
        flash("Användare skapad. Fortsätt med att logga in.")
        return redirect(url_for("login"))

    return render_template("register.html", title="Registrera", form=form, logged_in=current_user.is_authenticated)


@app.route("/login", methods=["POST", "GET"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if not user:
            flash(f"Mailadressen {form.email.data} finns inte registrerad hos oss. Försök igen.")
            return redirect(url_for("login"))

        if check_password_hash(user.password, form.password.data):
            login_user(user)
            flash(f"Välkommen {user.name}. Du är nu inloggad.")
            return redirect(url_for("home"))
        flash("Felaktigt lösenord. Försök igen.")
        return redirect(url_for("login"))

    return render_template("login.html", title="Logga in", form=form, logged_in=current_user.is_authenticated)


@app.route("/logout")
def logout():

    flash(f"Tack för besöket {current_user.name}. Du är nu utloggad.")
    logout_user()
    return redirect(url_for("home"))


# ------------------------------------------------------------------------------------------------------

# **********---------- POST ROUTES ----------**********

@app.route("/new-post", methods=["POST", "GET"])
@login_required
@admin_only
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        # | id | title | subtitle | date | body | img_url | author_id: Foreign Key |
        post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            date=date.today().strftime("%B %d, %Y"),
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user
        )
        db.session.add(post)
        db.session.commit()
        flash("Inlägget är sparat.")
        return redirect(url_for("home"))

    return render_template(
        "new-post.html",
        title="Nytt inlägg",
        form=form,
        current_user=current_user,
        logged_in=current_user.is_authenticated,
        user=current_user
    )


@app.route("/edit-post/<post_id>", methods=["POST", "GET"])
@login_required
@admin_only
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    form = PostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        body=post.body
    )
    if form.validate_on_submit():

        post.title = form.title.data
        post.subtitle = form.subtitle.data
        post.img_url = form.img_url.data
        post.body = form.body.data
        db.session.commit()
        flash("Inlägget är uppdaterat.")
        return redirect(url_for("show_post", post_id=post.id))

    return render_template(
        "edit-post.html",
        post_id=post.id,
        form=form,
        logged_in=current_user.is_authenticated,
        user=current_user
    )


@app.route("/show-post/<post_id>")
def show_post(post_id):
    user = None
    if current_user.is_authenticated:
        user = current_user
    post = BlogPost.query.get(post_id)
    return render_template(
        "show-post.html",
        title="Ska ändras",
        post=post,
        user=user,
        logged_in=current_user.is_authenticated
    )


@app.route("/comment-post/<post_id>", methods=["POST", "GET"])
@login_required
def comment_post(post_id):
    post = BlogPost.query.get(post_id)
    form = CommentForm()
    if form.validate_on_submit():
        # | id | text | post_id: Foreign Key | author_id: Foreign Key |
        comment = Comment(
            text=form.text.data,
            date=date.today().strftime("%B %d, %Y"),
            parent_post=post,
            comment_author=current_user
        )
        db.session.add(comment)
        db.session.commit()
        flash("Kommentaren är sparad.")
        return redirect(url_for("show_post", post_id=post.id))

    return render_template(
        "comment-post.html",
        form=form,
        current_user=current_user,
        logged_in=current_user.is_authenticated,
        user=current_user,
        post_id=post.id
    )


@app.route("/delete/<post_id>")
@login_required
@admin_only
def delete(post_id):
    post = BlogPost.query.get(post_id)
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for("home"))


@app.route("/delete-comment/<comment_id>")
@login_required
@admin_only
def delete_comment(comment_id):
    comment = Comment.query.get(comment_id)
    db.session.delete(comment)
    db.session.commit()
    flash("Kommentaren är raderad.")
    return redirect(url_for("home"))


# ------------------------------------------------------------------------------------------------------

# **********---------- STARTER ----------**********
if __name__ == "__main__":
    app.run()
    # app.run(debug=True)
    # app.run(host='0.0.0.0', port = 5000)

# TODO: Titles on the different sides.
# TODO: Mobile version - Navbar ugly with logged in as...
# TODO: Mobile version - Div to wide. Needs to be adjusted for mobile.
# TODO: Be able to change password
# TODO: Site contact
# TODO: Site About
