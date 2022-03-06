import functools

from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for

from werkzeug.security import check_password_hash, generate_password_hash

from flaskr.db import get_db


bp = Blueprint('auth', __name__, url_prefix='/auth')

# создает чертеж, который должен знать, где он находится (второй аргумент)
# url_prefix определяет урл по которому будет отображаться этот чертеж

@bp.route('/register', methods=('GET','POST'))
# ассоциирует урл с функцией. Когда фласк получает запрос по auth/register:
# он пользуется функцией и тем, что она возвращает
def register():
    # если пользователь заполняет форму, метод - пост, значит начинаем помещать информацию в базу данных
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None
        # обрабатываем отсутствие пароля или юзернейма
        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'

        if error is None:
            try:
                db.execute( # безопасное внесение в sqlite таблицу юзернейма и пассворда
                    "INSERT INTO user (username, password) VALUES (?, ?)",
                    (username, generate_password_hash(password))
                )
                db.commit() # закрепление изменений в  датабейзе
            except db.IntegrityError:
                error = f'User {username} already registered' #обработка ошибок если юзернейм уже существует
            else:
                return redirect(url_for('auth.login')) # при успешной регистрации отправляет на логин страниц


        flash(error) # корректно высвечивает ошибку

    return render_template('auth/register.html') # рендерит указанный хтмл документ


# за исключением комментариев делает то же самое что и предыдущая функция
@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None
        user = db.execute(
            'SELECT * FROM user WHERE username = ?',(username,)
        ).fetchone() # возвращает строку, если результат пустой, возвращает None

        if user is None:
            error = 'Username not found'
        elif not check_password_hash(user['password'], password):
            # сравнивает хэш пассворда уже существующего и введенного
            error = 'Wrong password'

        if error is None:
            session.clear() # словарь, который содержит айди валидированных сессий
            session['user_id'] = user['id']
            return redirect(url_for('index'))
        else:
            flash(error)

    return render_template('auth/login.html')


@bp.before_app_request
def load_logged_in_user():# функция, которая работает перед загрузкой любой страницы и проверяет
    # есть ли у чела открытая сессия, и если есть, помещает информацию юзера в g.user
    # который будет активен до конца реквеста
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute('SELECT * FROM user WHERE id = ?', (user_id,)).fetchone()


@bp.route('/logout') # удаляет текущую сессию и перенаправляет на начальную страницу
def logout():
    session.clear()
    return redirect(url_for('index'))


def login_required(view):
    # возвращает чела на логин страницу, если нет активной сессии
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)
    return wrapped_view
