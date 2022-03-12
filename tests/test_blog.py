import pytest
from flaskr.db import get_db

def test_index(client, auth):
    response = client.get('/')
    # убеждаемся, что таблички для перехода отображаются
    assert b'Log In' in response.data
    assert b'Register' in response.data

    auth.login()
    response = client.get('/')
    # убеждаемся, что есть логаут табличка
    assert b'Log Out' in response.data
    # убеждаемся, что пост корректно работает
    assert b'test title' in response.data
    assert b'by test on 2018-01-01' in response.data
    assert b'test\nbody' in response.data
    # убеждаемся, что мы сразу можем его изменить, т.к. залогинены уже
    assert b'href="/1/update"' in response.data

@pytest.mark.parametrize('path', (
    '/create',
    '/1/update',
    '/1/delete',
))
def test_login_required(client, path):
    # убеждаемся, что незалогиненый чел с ходу уезжает на логин страницу,
    # если для доступа к странице ему нужно быть залогиненым
    response = client.post(path)
    assert response.headers['Location'] == 'http://localhost/auth/login'

def test_author_required(app, client, auth):
    # меняем пользователя
    with app.app_context():
        db = get_db()
        db.execute('UPDATE post SET author_id = 2 WHERE id = 1')
        db.commit()

    auth.login()
    # не автопр поста не может изменять\удалять пост
    assert client.post('/1/update').status_code == 403
    assert client.post('/1/delete').status_code == 403
    # не автор поста не видит ссылки на изменение\удаление
    assert b'href="/1/update"' not in client.get('/').data

@pytest.mark.parametrize('path', (
    '/2/update',
    '/2/delete',
))
# проверяем, что попытка взаимодействия с несуществующим постом приводит к 404
def test_exists_required(client, auth, path):
    auth.login()
    assert client.post(path).status_code == 404


def test_create(client, auth, app):
    auth.login()
    assert client.get('/create').status_code == 200
    # страница работает
    client.post('/create', data={'title': 'created', 'body': ''})

    with app.app_context():
        db = get_db()
        count = db.execute('SELECT COUNT(id) FROM post').fetchone()[0]
        assert count == 2

def test_update(client, auth, app):
    auth.login()
    assert client.get('/1/update').status_code == 200
    # страница работает
    client.post('/1/update', data={'title': 'updated', 'body': ''})

    with app.app_context():
        db = get_db()
        post = db.execute('SELECT * FROM post WHERE id = 1').fetchone()
        # убеждаемся, что пост действительно был апдейтнут
        assert post['title'] == 'updated'

def test_delete(client, auth, app):
    auth.login()
    response = client.post('/1/delete')
    # удаляем
    assert response.headers['Location'] == 'http://localhost/'
    # проверяем верность редиректа

    with app.app_context():
        db = get_db()
        post = db.execute('SELECT * FROM post WHERE id = 1').fetchone()
        # проверяем что поста нет после удаления
        assert post is None

def test_upvote(client, auth, app):
    auth.login()
    # перед тестом строка в таблице кармы еще не создана
    with app.app_context():
        db = get_db()
        karma = db.execute('SELECT * FROM carma WHERE user_id = 1').fetchone()
        assert karma is None
    assert client.get('/1/upvote').status_code == 302
    response = client.post('/1/upvote')
    assert response.headers['Location'] == 'http://localhost/'
    with app.app_context():
        db = get_db()
        karma = db.execute('SELECT * FROM carma WHERE user_id = 1').fetchone()
        assert karma is not None
    with app.app_context():
        db = get_db()
        # выставляем карму и выставляем значение ГОЛОСОВАЛ -
        db.execute('UPDATE carma SET voted = 2 WHERE user_id = 1')
        db.execute('UPDATE post SET carma = - 1 WHERE id = 1')
        #апвоутим
        client.post('/1/upvote')
        right_count = db.execute('SELECT * FROM post WHERE carma = 1').fetchone()
        assert right_count is not None
        karma = db.execute('SELECT * FROM carma WHERE voted = 1').fetchone()
        assert karma is not None
        # карма должна стать +1, значение - ГОЛОСОВАЛ +
        client.post('/1/upvote')
        # апвоутим
        karma = db.execute('SELECT * FROM carma WHERE voted = 0').fetchone()
        assert karma is not None
        right_count = db.execute('SELECT * FROM post WHERE carma = 0').fetchone()
        assert right_count is not None
        # карма становится 0, значение НЕ ГОЛОСОВАЛ
        client.post('/1/upvote')
        # апвоутим
        karma = db.execute('SELECT * FROM carma WHERE voted = 1').fetchone()
        assert karma is not None
        right_count = db.execute('SELECT * FROM post WHERE carma = 1').fetchone()
        assert right_count is not None
        # проверяем, что карма выросла а значение стало ГОЛОСОВАЛ +


def test_downvote(client, auth, app):
    auth.login()
    # перед тестом строка в таблице кармы еще не создана
    with app.app_context():
        db = get_db()
        karma = db.execute('SELECT * FROM carma WHERE user_id = 1').fetchone()
        assert karma is None
    assert client.get('/1/downvote').status_code == 302
    response = client.post('/1/downvote')
    assert response.headers['Location'] == 'http://localhost/'
    with app.app_context():
        db = get_db()
        karma = db.execute('SELECT * FROM carma WHERE user_id = 1').fetchone()
        assert karma is not None
    with app.app_context():
        db = get_db()
        # выставляем карму и выставляем значение ГОЛОСОВАЛ +
        db.execute('UPDATE carma SET voted = 1 WHERE user_id = 1')
        db.execute('UPDATE post SET carma = 1 WHERE id = 1')
        #даунвоутим
        client.post('/1/downvote')
        right_count = db.execute('SELECT * FROM post WHERE carma = -1').fetchone()
        assert right_count is not None
        karma = db.execute('SELECT * FROM carma WHERE voted = 2').fetchone()
        assert karma is not None
        # карма должна стать -1, значение - ГОЛОСОВАЛ -
        client.post('/1/downvote')
        #даунвоутим
        karma = db.execute('SELECT * FROM carma WHERE voted = 0').fetchone()
        assert karma is not None
        right_count = db.execute('SELECT * FROM post WHERE carma = 0').fetchone()
        assert right_count is not None
        # карма становится 0, значение НЕ ГОЛОСОВАЛ
        client.post('/1/downvote')
        # даунвоутим
        karma = db.execute('SELECT * FROM carma WHERE voted = 2').fetchone()
        assert karma is not None
        right_count = db.execute('SELECT * FROM post WHERE carma = -1').fetchone()
        assert right_count is not None
        # проверяем, что карма упала а значение стало ГОЛОСОВАЛ -



