import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') #or 'opiu'
    SSL_DISABLE = False
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True
    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    QUIZ_MAIL_SUBJECT_PREFIX = '[Korean Level Up]'
    QUIZ_MAIL_SENDER = 'Admin <koreanlevelup@gmail.com>'
    QUIZ_ADMIN = os.environ.get('QUIZ_ADMIN')
    QUIZ_SLOW_DB_QUERY_TIME=0.5
    QUIZ_POSTS_PER_PAGE = 10

    STRIPE_PUBLISHABLE_KEY=os.environ.get('STRIPE_PUBLISHABLE_KEY')
    STRIPE_SECRET_KEY=os.environ.get('STRIPE_SECRET_KEY')

    @staticmethod
    def init_app(app):
        pass

    
class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data-test.sqlite')
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') #or \
     #   'sqlite:///' + os.path.join(basedir, 'data.sqlite')
    
    #SQLALCHEMY_DATABASE_URI = 'postgresql://newuser:jieun@localhost/hangulappdb'

    WTF_CSRF_ENABLED = True

class HerokuConfig(ProductionConfig):
    @classmethod
    def init_app(cls, app):
        ProductionConfig.init_app(app)
        from werkzeug.contrib.fixers import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app)
        import logging
        from logging import StreamHandler
        file_handler = StreamHandler()
        file_handler.setLevel(logging.WARNING)
        app.logger.addHandler(file_handler)


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,

    'default': HerokuConfig
    #'default': ProductionConfig
}
