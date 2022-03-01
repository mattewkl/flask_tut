import sqlite3

import click
from flask import current_app, g
from flask.cli import with_appcontext

# g - уникальный объект, который содержит информацию к которой могут обратиться разные функции

def get_db():
    # current_app указывает на приложение, которое обрабатывает запрос.
    # При вызове get_db() фласк может пользоваться этим объектом
    # вместо создания новой связи каждый раз, связь используется снова, если функция вызвана дважды в одном рекветсе
    if 'db' not in g:
        g.db = sqlite3.connect(
            # создает соединение с sqlite базой данных,
            # и создает сам файл, если его еще не существует
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
        # дает возврат строк как словарей, чтобы к ним можно было
        # обратиться по имени ????



    return g.db

def close_db(e=None):
    # если есть активное соединение - закрывает его.
    db = g.pop('db',None)

    if db is not None:
        db.close()

def init_db():
    db = get_db()

    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf-8'))

@click.command('init_db')
@with_appcontext
def init_db_command():
    # очищаем существующие таблицы, и создаем новые
    init_db()
    click.echo('Датабэй инициализирован')

def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
