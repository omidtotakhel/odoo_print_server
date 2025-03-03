import flask
from flask import request

from model.server import Server
from model.server_job import ServerJob
from model.user import User
from server.print_server import PrintServer

main = flask.Blueprint('main', __name__)
import model.base as base

user = False
cups = False
odoo = False
completed_jobs = []
printers = {}


@main.route('/')
def index():
    # user = User.search({'username': 'admin'}, limit=1)
    # odoo = base.get_odoo_from_user(user)
    # cups = base.get_cups_from_user(user)
    # print_server = PrintServer(odoo_server=odoo, cups_server=cups)
    # printers = print_server.get_printer_list()
    # printer = printers.get("Star_SP742")
    # cut_command = b'\x1D\x56\x00'
    # if printer:
    #     printer.print_document(b"Help\nHelp\nHelp\n")
    return flask.render_template('base/index.html')


@main.route('/printing')
def printing_index():
    return flask.redirect(flask.url_for('main.printers_list'))
    printers = {}
    if flask.g.cups:
        printers = flask.g.cups.get_printers()
    return flask.render_template("printing/index.html", printers=printers.values())


@main.route('/printers')
def printers_list():
    printers = {}
    if flask.g.cups:
        printers = flask.g.cups.get_printers()
    return flask.render_template("printing/printers.html", printers=printers.values())


def get_user(odoo):
    return odoo.search("res.users", domain=[['id', '=', odoo.uid]], fields=['display_name', 'login'])


@main.before_request
def inject_globals():
    """ Inject variable only for specific routes """
    username = flask.session.get('username')
    print("Session Username ", username)
    if not username:
        return flask.redirect(flask.url_for('auth.login'))

    user = User.search(domain={'username': username}, limit=1)

    if not user:
        print("User object ", user)
        return flask.redirect(flask.url_for('auth.login'))
    flask.g.odoo = base.get_odoo_from_user(user)
    flask.g.cups = base.get_cups_from_user(user)
    flask.g.user = user


@main.route('/error')
def error():
    return flask.render_template("base/error.html")


@main.route('/settings')
def settings():
    return flask.redirect(flask.url_for('main.users'))


@main.route('/terminals')
def terminals():
    return flask.render_template('terminal/terminals.html')


@main.route('/users')
def users():
    users = User.search()
    return flask.render_template("settings/users.html", users=users)


@main.route('/servers', methods=['GET'])
def servers():
    servers = Server.search() or []
    return flask.render_template("settings/servers.html", servers=servers)


@main.route('/new_server', methods=['GET'])
def new_server():
    identifier = request.values.get("identifier")
    server = False
    if identifier:
        server = Server.search({'identifier': identifier}, limit=1)
    return flask.render_template("settings/server_form.html", server=server)


@main.route('/servers', methods=['POST'])
def server_post():
    identifier = request.form.get('identifier')
    if not identifier:
        return flask.redirect(flask.url_for('main.error'))

    payload = {
        'name': request.form.get('name'),
        'identifier': identifier,
        'location': request.form.get('location'),
        'active': request.form.get('active')
    }
    print("Server ", )
    domain = {
        'identifier': identifier
    }

    server = Server.search(domain=domain, limit=1)
    if not server:
        Server.create(payload)
        print("Creating Server =========== ")
    else:
        server.write(data=payload)

    return flask.redirect(flask.url_for('main.servers'))


@main.route('/print_jobs')
def print_jobs():
    jobs = ServerJob.search()
    return flask.render_template("printing/jobs.html", jobs=jobs)


@main.route("/unlink_user/<user_id>")
def unlink_user(user_id):
    print("User id ", user_id)
    user = User.search({'id': user_id}, limit=1)
    user.unlink()
    return flask.redirect(flask.url_for("main.users"))


@main.route("/unlink_server/<identifier>")
def unlink_server(identifier):
    server = Server.search({'identifier': identifier}, limit=1)
    server.unlink()
    return flask.redirect(flask.url_for("main.servers"))

@main.route("/toggle_server/<identifier>")
def toggle_server(identifier):
    server = Server.search(domain={'identifier': identifier}, limit=1)
    server.write({'active': not server.active})
    return flask.redirect(flask.url_for("main.servers"))

@main.route("/toggle/<int:user_id>")
def toggle(user_id):
    user = User.search(domain={'user_id': user_id}, limit=1)
    user.write({'active': not user.active})
    return flask.redirect(flask.url_for("main.users"))
