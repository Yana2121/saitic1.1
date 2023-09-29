from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, current_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash
from models import User, db, Category, Tag, Post

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'secret-key-goes-here'
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('profile'))
    else:
        return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('profile'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('profile'))
        else:
            flash('Неправильное имя пользователя или пароль')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('profile'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        user = User.query.filter_by(username=username).first()
        if user:
            flash('Данное имя пользователя уже занято')
        else:
            hashed_password = generate_password_hash(password)
            new_user = User(username=username, password=hashed_password, email=email)
            db.session.add(new_user)
            db.session.commit()
            flash('Аккаунт успешно создан!')
            return redirect(url_for('login'))
    return render_template('register.html')



@app.route('/profile')
def profile():
    if current_user.is_authenticated:
        return render_template('profile.html', user=current_user)
    else:
        return redirect(url_for('login'))

@app.route('/all_posts')
def all_posts():
    posts = Post.newest_blog().all()
    return render_template('all_posts.html', posts=posts)

@app.route('/post/<int:post_id>')
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', post=post)


@app.route('/category/<int:category_id>')
def category(category_id):
    category = Category.query.get_or_404(category_id)
    posts = Post.query.filter_by(category_id=category_id).order_by(Post.date.desc()).all()
    return render_template('category.html', category=category, posts=posts)

@app.route('/tag/<int:tag_id>')
def tag(tag_id):
    tag = Tag.query.get_or_404(tag_id)
    posts = Post.query.filter(Post.tags.any(id=tag_id)).order_by(Post.date.desc()).all()
    return render_template('tag.html', tag=tag, posts=posts)

@app.route('/new_post', methods=['GET', 'POST'])
def new_post():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        category_id = request.form['category']
        tag_ids = [int(tag_id) for tag_id in request.form.getlist('tags')]
        post = Post(title=title, content=content, category_id=category_id)
        for tag_id in tag_ids:
            tag = Tag.query.get(tag_id)
            post.tags.append(tag)
        db.session.add(post)
        db.session.commit()
        flash('Запись создана!', 'success')
        return redirect(url_for('all_posts'))
    categories = Category.query.all()
    tags = Tag.query.all()
    return render_template('new_post.html', categories=categories, tags=tags)

@app.route('/edit_post/<int:post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    if request.method == 'POST':
        post.title = request.form['title']
        post.content = request.form['content']
        post.category_id = request.form['category']
        tag_ids = [int(tag_id) for tag_id in request.form.getlist('tags')]
        post.tags = []
        for tag_id in tag_ids:
            tag = Tag.query.get(tag_id)
            post.tags.append(tag)
        db.session.commit()
        flash('Запись обновлена!', 'success')
        return redirect(url_for('all_posts'))
    categories = Category.query.all()
    tags = Tag.query.all()
    return render_template('edit_post.html', post=post, categories=categories, tags=tags)

@app.route('/delete_post/<int:post_id>', methods=['GET', 'POST'])
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    flash('Запись удалена!', 'success')
    return redirect(url_for('all_posts'))
    
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
