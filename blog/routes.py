"""

This handles all the routes for the site
Here we can control how users will move between
pages, and set parameters that restrict or
allow access

"""

from flask import render_template, url_for, flash, redirect, request, abort
from blog.forms import RegistrationForm, LoginForm, UpdateProfileForm, PostForm
from blog.models import User, Post
from blog import app, db, bcrypt
import secrets
import os
from flask_login import login_user, logout_user, current_user, login_required
from PIL import Image


# The front page of the site. First thing users will see
@app.route("/")
@app.route("/home")
def home():
	page = request.args.get('page', 1, type=int)
	posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=5)
	return render_template('home.html', title='Home', posts=posts)

@app.route("/login", methods=['GET', 'POST'])
def login():
	# If user is already logged in go to home page
	if current_user.is_authenticated:
		return redirect(url_for('home'))
	form = LoginForm()
	# Check if data entered by user matches data in User table
	if form.validate_on_submit():
		user = User.query.filter_by(username=form.username.data).first()
		if user and bcrypt.check_password_hash(user.password, form.password.data):
			login_user(user, remember=form.remember.data)
			# Take user to page they were headed to before logging in
			next_page = request.args.get('next')
			return redirect(next_page) if next_page else redirect(url_for('home'))
		# If incorrect info entered, flash error message
		else:
			flash('Login Unsuccessful. Please check username and password', 'danger')
	return render_template('login.html', title='Login', form=form)

# Logout option redirects to home page
@app.route("/logout")
def logout():
	logout_user()
	return redirect(url_for('home'))


@app.route("/register", methods=['GET', 'POST'])
def register():
	# If user already logged in go to home page
	if current_user.is_authenticated:
		return redirect(url_for('home'))
	form = RegistrationForm()
	if form.validate_on_submit():
		# Hash password
		hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
		# Pass info into their respective columns
		user = User(username=form.username.data, email=form.email.data, password=hashed_password)
		# And save info in User table
		db.session.add(user)
		db.session.commit()
		flash(f'profile created for {form.username.data}!', 'success')
		# Once succesfully registered, take user to login page
		return redirect(url_for('login'))
	return render_template('register.html', title='Register', form=form)

# Define a function to handle saving profile pictures uploaded by users
# Will be used in profile route
def save(form_picture):
	# Save random number in variable
	random = secrets.token_hex(8)
	# Split the pathname path into a pair (root, ext)
	_, f_ext = os.path.splitext(form_picture.filename)
	# Save in variable the random number with the ext to create new name for image uploaded (don't keep the orig filename)
	p_filename = random + f_ext
	# Folder where pictures are saved
	p_path = os.path.join(app.root_path, 'static/pics', p_filename)
	# Set size for all uploaded pictures
	size = (125, 125)
	i = Image.open(form_picture)
	i.thumbnail(size)
	i.save(p_path)
	return p_filename

@app.route("/profile", methods=['GET', 'POST'])
@login_required
def profile():
	# Form created so users can update acct info
	form = UpdateProfileForm()
	if form.validate_on_submit():
		# Pass form information into db
		if form.picture.data:
			current_user.image_file = save(form.picture.data)
		current_user.username = form.username.data
		current_user.email = form.email.data
		db.session.commit()
		flash('Profile updated', 'success')
		return redirect(url_for('profile'))
	elif request.method == 'GET':
		form.username.data = current_user.username
		form.email.data = current_user.email
	image_file = url_for('static', filename='pics/' + current_user.image_file)
	return render_template('profile.html', title='profile', image_file=image_file, form=form)

# New blog entries
@app.route("/post/new", methods=['GET', 'POST'])
@login_required
def new_post():
	# Form created in forms.py
	form = PostForm()
	if form.validate_on_submit():
		# Form input saved into db
		post = Post(title=form.title.data, content=form.content.data, writer=current_user)
		db.session.add(post)
		db.session.commit()
		flash('Post created', 'success')
		return redirect(url_for('home'))
	return render_template('newpost.html', title='New Post', form=form, legend='New Post')

# Page to view individual blog entries
@app.route("/post/<int:post_id>")
def post(post_id):
	post = Post.query.get_or_404(post_id)
	return render_template('post.html', title=post.title, post=post)

# Make changes to blog entries
@app.route("/post/<int:post_id>/update", methods=['GET', 'POST'])
@login_required
def update_post(post_id):
	post = Post.query.get(post_id)
	# Don't allow changes if the current user is not the orig author of the post
	if post.writer != current_user:
		abort(403)
	form = PostForm()
	# If changes submitted, send changes to db
	if form.validate_on_submit():
		post.title = form.title.data
		post.content = form.content.data
		db.session.commit()
		flash('Post has been updated', 'success')
		return redirect(url_for('post', post_id=post_id))
	# If arrived on page via GET, show the form with the undedited blog entry
	elif request.method == 'GET':
		form.title.data = post.title
		form.content.data = post.content
	return render_template('newpost.html', title='Update Post', form=form, legend='Update Post')

# Delete a blog post
@app.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
	post = Post.query.get(post_id)
	# Make blog entry belongs to current user
	if post.writer != current_user:
		abort(403)
	db.session.delete(post)
	db.session.commit()
	flash('Post has been deleted', 'success')
	return redirect(url_for('home'))

# Delete a user
@app.route("/profile/<string:username>/delete", methods=['POST'])
@login_required
def delete_acct(username):
	user = User.query.filter_by(username=username).first()
	db.session.delete(user)
	db.session.commit()
	flash('User has been deleted', 'success')
	return redirect(url_for('home'))

# Show all blog posts for an indivisual user
@app.route("/user/<string:username>/")
def user_posts(username):
	page = request.args.get('page', 1, type=int)
	user = User.query.filter_by(username=username).first()
	posts = Post.query.filter_by(writer=user).order_by(Post.date_posted.desc()).paginate(page=page, per_page=5)
	return render_template('user.html', posts=posts, user=user)