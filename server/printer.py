import errno
import logging
import os
from tempfile import mkstemp

_logger = logging.getLogger(__name__)

try:
    import cups
except ImportError:
    _logger.debug("Cannot `import cups`.")

encryption_policy = [
    ("0", "HTTP_ENCRYPT_IF_REQUESTED"),
    ("1", "HTTP_ENCRYPT_NEVER"),
    ("2", "HTTP_ENCRYPT_REQUIRED"),
    ("3", "HTTP_ENCRYPT_ALWAYS"),
]


class Printer:

    def __init__(self, server, printer_info):
        self.server = server
        printer = self._prepare_update_from_cups(printer_info)
        self.name = printer.get("name", "Printer")
        self.model = printer.get("model")
        self.location = printer.get("location")
        self.uri = printer.get("uri")
        self.status = printer.get("status")
        self.status_message = printer.get("status_message")
        self.system_name = False
        self.options = {}

    def get_vals(self):
        return {
            'name': self.name,
            'code': self.system_name,
            'ip_address': self.uri,
            'location': self.location
        }

    def set_system_name(self, name):
        self.system_name = name

    def _prepare_update_from_cups(self, cups_printer):
        mapping = {3: "available", 4: "printing", 5: "error"}
        cups_vals = {
            "name": cups_printer["printer-info"],
            "model": cups_printer.get("printer-make-and-model", False),
            "location": cups_printer.get("printer-location", False),
            "uri": cups_printer.get("device-uri", False),
            "status": mapping.get(cups_printer.get("printer-state"), "unknown"),
            "status_message": cups_printer.get("printer-state-message", ""),
        }

        # prevent write if the field didn't change
        vals = {
            fieldname: value
            for fieldname, value in cups_vals.items()
        }

        printer_uri = cups_printer["printer-uri-supported"]
        printer_system_name = printer_uri[printer_uri.rfind("/") + 1:]
        connection = self.server._open_connection()
        ppd_info = connection.getPPD3(printer_system_name)
        ppd_path = ppd_info[2]
        if not ppd_path:
            return vals

        ppd = cups.PPD(ppd_path)
        option = ppd.findOption("InputSlot")
        try:
            os.unlink(ppd_path)
        except OSError as err:
            if err.errno != errno.ENOENT:
                raise
        if not option:
            return vals

        tray_commands = []
        cups_trays = {
            tray_option["choice"]: tray_option["text"] for tray_option in option.choices
        }

        tray_commands.extend(
            [
                {"name": text, "system_name": choice}
                for choice, text in cups_trays.items()
            ]
        )

        if tray_commands:
            vals["tray_ids"] = tray_commands
        return vals

    def print_document(self, content, **print_opts):
        fd, file_name = mkstemp()
        if isinstance(content, str):
            content = content.encode()
        try:
            os.write(fd, content)
        finally:
            os.close(fd)
        return self.print_file(file_name, **print_opts)

    def print_file(self, file_name, **print_opts):
        """Print a file"""
        title = print_opts.pop("title", file_name)
        connection = self.server._open_connection()
        options = self.get_options()
        print("Options ", options)
        connection.printFile(self.system_name,
                             file_name,
                             title,
                             options=options)
        _logger.info(
            "Printing job: '{}' on {}".format(file_name, self.server.url)
        )
        try:
            os.remove(file_name)
        except OSError as exc:
            _logger.warning("Unable to remove temporary file %s: %s", file_name, exc)
        return True


    def get_options(self):
        options = {'behavior': "{'action': 'server', 'tray': False}"}
        for key, value in self.options.items():
            options[key] = value
        return options

    def set_options(self, options):
        for key, value in options.items():
            self.options[key] = value
        return True

    def cancel_all_jobs(self, purge_jobs=False):
        connection = self.server._open_connection()
        connection.cancelAllJobs(name=self.system_name, purge_jobs=purge_jobs)
        return True

    def disable_printer(self):
        connection = self.server._open_connection()
        connection.disablePrinter(self.system_name)
        return True

    def enable_printer(self):
        connection = self.server._open_connection()
        connection.enablePrinter(self.system_name)
        return True
