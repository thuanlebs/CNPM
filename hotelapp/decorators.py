from functools import wraps
from flask import request, redirect, url_for
from flask_login import current_user
import models

def loggedin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated:
            return redirect(url_for('index'))

        return f(*args, **kwargs)

    return decorated_function


def staffonly(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role == models.UserRole.CUSTOMER:
            return redirect(url_for('login', next=request.url))

        return f(*args, **kwargs)

    return decorated_function
