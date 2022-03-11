from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint('blog', __name__)


@bp.route('/')
def index():
    db = get_db()
    posts = db.execute(
        """SELECT p.id, title, body, created, author_id, username, carma
        FROM post p JOIN user u ON p.author_id = u.id
        ORDER BY created DESC""").fetchall()
    return render_template('blog/index.html', posts=posts)


def get_post(id, check_author=True):
    """Get a post and its author by id.
    Checks that the id exists and optionally that the current user is
    the author.
    :param id: id of post to get
    :param check_author: require the current user to be the author
    :return: the post with author information
    :raise 404: if a post with the given id doesn't exist
    :raise 403: if the current user isn't the author
    """
    post = (
        get_db()
        .execute(
            "SELECT p.id, title, body, created, author_id, username"
            " FROM post p JOIN user u ON p.author_id = u.id"
            " WHERE p.id = ?",
            (id,),
        )
        .fetchone()
    )

    if post is None:
        abort(404, f"Post id {id} doesn't exist.")

    if check_author and post["author_id"] != g.user["id"]:
        abort(403)

    return post

@bp.route('/create', methods=("GET", "POST"))
@login_required
def create():
    """Create a new post for the current user."""
    if request.method == "POST":
        title = request.form["title"]
        body = request.form["body"]
        carma = 1
        error = None

        if not title:
            error = "Title is required."

        if error is  None:
            db = get_db()
            db.execute(
                "INSERT INTO post (title, body, author_id, carma) VALUES (?, ?, ?, ?)",
                (title, body, g.user["id"], carma),
            )
            db.commit()
            return redirect(url_for("blog.index"))
        else:
            flash(error)


    return render_template("blog/create.html")

@bp.route('/<int:id>/update', methods=('GET','POST'))
@login_required
def update(id):
    post = get_post(id)

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Без заголовка не получится'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute("UPDATE post SET title = ?, body = ? WHERE id = ?;", (title, body, id))
            db.commit()

            return redirect(url_for('blog.index'))
    return render_template('blog/update.html',post=post)


@bp.route('/<int:id>/upvote', methods=('POST', 'GET'))
@login_required
def upvote(id):
    get_post(id)
    db = get_db()
    db.execute('UPDATE post '
               'SET carma = carma + 1 '
               'WHERE id = ?', (id,))
    db.commit()

    return redirect(url_for('blog.index'))


@bp.route('/<int:id>/downvote', methods=('POST','GET'))
@login_required
def downvote(id):
    get_post(id)
    db = get_db()
    db.execute('UPDATE post '
               'SET carma = carma - 1 '
               'WHERE id = ?', (id,))
    db.commit()

    return redirect(url_for('blog.index'))

@bp.route('/<int:id>/delete',methods=('POST',))
@login_required
def delete(id):
    get_post(id)
    db = get_db()
    db.execute('DELETE FROM post WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('blog.index'))