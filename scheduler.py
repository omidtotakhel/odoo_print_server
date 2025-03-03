import threading
import time

import model.base as base
from model.server import Server
from model.session import ClientSession
from model.user import User
from server.print_server import PrintServer
from setup import app

# Todo: Make this dynamic
clients = {}


def run_scheduler():
    while True:
        time.sleep(5)  # Simulate external job check interval
        with app.app_context():
            clients = ClientSession.search(domain={})
            for client in clients:
                client.update_scheduler_state(False)

            users = User.search(domain={})
            for user in users:
                threading.Thread(target=job_scheduler, args=[user]).start()


def job_scheduler(user_obj):
    with app.app_context():
        username = user_obj.username
        scheduler_id = ClientSession.search({'client_id': username}, limit=1)
        if not scheduler_id:
            scheduler_id = ClientSession.create({'client_id': username})

        scheduler_status = scheduler_id.scheduler_status

        # Check if Scheduler is already running and prevent duplicated threads
        if scheduler_status:
            return

        scheduler_id.update_scheduler_state(True)

        job_processed = []

        if not user_obj:
            return job_processed
        try:
            client = clients.get(username)

            if not client:
                clients[username] = {'odoo': False, 'cups': False}
                client = clients[username]

            odoo = client.get('odoo')
            if not odoo:
                odoo = base.get_odoo_from_user(user_obj)
                clients[username]['odoo'] = odoo

            cups = client.get('cups')
            if not cups:
                cups = base.get_cups_from_user(user_obj)
                clients[username]['cups'] = cups

            error = False
            if not odoo and not cups:
                error = "Could not connect to cups and odoo server."
            elif not odoo:
                error = "Could not connect to Odoo"
            elif not cups:
                error = "Could not connect to Cups Server"

            if not error:
                servers = Server.search(domain={"active": True})
                active_server = [server.identifier for server in servers]
                if not active_server:
                    print("No Active Server")
                    return
                print_server = PrintServer(cups_server=cups, odoo_server=odoo)
                job_processed = print_server.sync_server_jobs(username, active_server)

        except Exception as e:
            print("Exception ", e)
        scheduler_id.update_scheduler_state(False)
        return job_processed
