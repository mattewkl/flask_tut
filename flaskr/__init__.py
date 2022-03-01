from flask import Flask
import os

def create_app(test_config=None):
    # функция создания и настройки приложения
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path,'flaskr.sqlite')
    )

    if test_config is None:
        # если не идет тестирование, загружаем файл конфигурации
        app.config.from_pyfile('config.py',silent=True)
    else:
        # конфигурация тестирования если идет тестирование
        app.config.from_mapping(test_config)


    # убеждаемся что папка instance существует
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # страница с простым возвратом текста
    @app.route('/hello')
    def hello():
        return 'HELLOOOOOO'

    from . import db
    db.init_app(app)

    from . import auth
    app.register_blueprint(auth.bp) # регистрирует чертеж auth

    from . import blog
    app.register_blueprint(blog.bp)
    app.add_url_rule('/', endpoint='index')


    return app


