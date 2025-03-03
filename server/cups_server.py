# Copyright (C) 2016 SYLEAM (<http://www.syleam.fr>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from server.printer import Printer
import cups

cups_server = cups

_logger = logging.getLogger(__name__)



encryption_policy = [
    ("0", "HTTP_ENCRYPT_IF_REQUESTED"),
    ("1", "HTTP_ENCRYPT_NEVER"),
    ("2", "HTTP_ENCRYPT_REQUIRED"),
    ("3", "HTTP_ENCRYPT_ALWAYS"),
]


class CupsServer:

    def __init__(self, url, port, user, password, encryption_policy=None):
        self.url = url
        self.port = port
        self.user = user
        self.password = password
        self.encryption_policy = encryption_policy

    def _open_connection(self):
        connection = False
        # Password callback
        password = self.password

        def pw_callback(prompt):
            return password

        try:

            cups.setServer(self.url)
            cups.setPort(self.port)

            if self.user:
                cups.setUser(self.user)
                if self.encryption_policy:
                    cups.setEncryption(int(self.encryption_policy))
                if self.password:
                    cups.setPasswordCB(pw_callback)
            connection = cups.Connection(host=self.url, port=self.port)

        except Exception as e:
            message = (
                          "Failed to connect to the CUPS server on %(address)s:%(port)s. "
                          "Check that the CUPS server is running and that "
                          "you can reach it from the Odoo server."
                      ) % {
                          "address": self.url,
                          "port": self.port,
                      }
            _logger.warning(message)
            print("Error ", e)
            return connection
        return connection

    def get_printer_list(self):
        connection = self._open_connection()
        printers = connection.getPrinters()
        return printers

    def update_jobs(self, which="all", first_job_id=-1):
        mapping = {
            3: "pending",
            4: "pending held",
            5: "processing",
            6: "processing stopped",
            7: "canceled",
            8: "aborted",
            9: "completed",
        }
        connection = self._open_connection()
        if not connection:
            return

            # Retrieve asked job data
        jobs_data = connection.getJobs(
            which_jobs=which,
            first_job_id=first_job_id,
            requested_attributes=[
                "job-name",
                "job-id",
                "printer-uri",
                "job-media-progress",
                "time-at-creation",
                "job-state",
                "job-state-reasons",
                "time-at-processing",
                "time-at-completed",
            ],
        )
        return True

    def get_printers(self):
        printers = self.get_printer_list()
        printer_list = {}
        for name, printer_info in printers.items():
            printer = Printer(self, printer_info)
            printer.set_system_name(name)
            printer_list[name] = printer
        return printer_list
