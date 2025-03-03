from flask import session, Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash

import model.base as base

auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET'])
def login():
    return render_template("auth/auth_odoo.html")


@auth.route('/login', methods=['POST'])
def login_post():
    try:
        payload = {
            'url': request.form.get('url'),
            'db': request.form.get('db'),
            'username': request.form.get('username'),
            'password': request.form.get('password')
        }

        odoo = base.validate_odoo(payload)
        if odoo.rpc:
            session['username'] = odoo.username
            return redirect(url_for('auth.login_cups'))
        flash("Could not connect to Odoo. Make sure the information entered are correct.", 'error')
        return redirect(url_for('auth.login'))
    except Exception as e:
        print("Login: Error ", e)
        flash("Could not connect to Odoo. " + str(e), 'error')
        return redirect(url_for('auth.login', **{'error': e}))


@auth.route('/login_cups', methods=['GET'])
def login_cups():
    return render_template("auth/auth_cups.html")


@auth.route('/login_cups', methods=['POST'])
def login_cups_post():
    try:
        payload = {
            'url': request.form.get('url'),
            'port': int(request.form.get('port')),
            'user': request.form.get('username'),
            'password': request.form.get('password')
        }
        cups = base.validate_cups(payload)
        if cups:
            return redirect(url_for('main.index'))
        flash("Could not connect to CUPS Server. Make sure the information entered are correct.", 'error')
        return redirect(url_for('auth.login_cups'))
    except Exception as e:
        print("Login CUPS: Error ", e)
        flash(str(e), 'error')
        return redirect(url_for('auth.login_cups'))


def is_password_correct(password, user_password):
    return check_password_hash(password, user_password)


def set_password(password):
    return generate_password_hash(password)


@auth.route('/logout')
def logout():
    return 'Logout'
