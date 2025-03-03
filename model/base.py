from flask import session

from model.user import User
from server.cups_server import CupsServer
from server.odoo import Odoo


def get_cups_from_user(user):
    cups = False
    data = {
        'url': user.cups_url,
        'port': user.cups_port,
        'user': user.cups_username,
        'password': user.cups_password,
    }

    try:
        print("user ", user)
        print("Cups Data ", data)
        cups = CupsServer(**data)
        connection = cups._open_connection()
        if not connection:
            return False
    except Exception as e:
        print("User Cups: Error ", e)
    return cups


def get_odoo_from_user(user):
    odoo = False
    try:
        odoo = Odoo(
            url=user.url,
            db=user.db,
            username=user.username,
            password=user.password,
        )
        if not odoo.rpc:
            return False
    except Exception as e:
        print("User Odoo: Error ", e)
    return odoo


def validate_cups(payload):
    print("Login CUPS: Payload ", payload)
    cups = CupsServer(**payload)
    connection = cups._open_connection()
    if connection:
        username = session.get('username')
        user = User.search(domain={'username': username}, limit=1)

        res = user.write(data={
            'cups_url': payload.get('url'),
            'cups_port': payload.get('port'),
            'cups_username': payload.get('user'),
            'cups_password': payload.get('password')
        })
        if res:
            print("Login CUPS: Successful as ", payload.get('user'))
            session['cups_username'] = payload.get('user')
    if connection:
        return cups
    return False


def validate_odoo(payload):
    print("Login: Payload ", payload)
    odoo = Odoo(**payload)
    username = payload.get('username')
    print("Login: Odoo RPC ", odoo.rpc)
    if odoo.rpc:
        domain = {
            'username': username
        }
        print("login: Passing domain ", domain)
        user = User.search(domain=domain, limit=1)
        if not user:
            User.create(payload)
        else:
            user.write(data=payload)
        session['username'] = username
        print("Login: Successful as ", username)
    print("Login: Odoo RPC ", odoo.rpc)
    return odoo


def get_user(odoo):
    return odoo.search("res.users", domain=[['id', '=', odoo.uid]], fields=['display_name', 'login'])
