from functools import wraps

from flask import session
from flask import redirect
from flask import url_for

def login_required(f):

    @wraps(f)
    def decorated(*args, **kwargs):

        if "user_id" not in session:

            return redirect(
                url_for("auth.login")
            )

        return f(*args, **kwargs)

    return decorated


def profile_required(f):

    @wraps(f)
    def decorated(*args, **kwargs):

        if not session.get(
            "is_profile_complete",
            False
        ):

            return redirect(
                url_for("auth.profil")
            )

        return f(*args, **kwargs)

    return decorated