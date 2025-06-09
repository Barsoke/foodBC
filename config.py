
import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('a-string-secret-at-least-256-bits-long') or 'a-string-secret-at-least-256-bits-long'

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'foodexpress.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_SECRET_KEY = os.environ.get('a-string-secret-at-least-256-bits-long') or 'a-string-secret-at-least-256-bits-long'
