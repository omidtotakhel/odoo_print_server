import base64
import io
import logging
import socket

import requests
from PIL import Image

from model.server_job import ServerJob

server_codes = ['10001', '10002']
PRINT_SERVER_JOB = "print.server.job"
PRINT_SERVER = 'print.server'
PRINT_SERVER_PRINTER = 'print.server.printer'
blocklist_jobs = []

logger = logging.getLogger(__name__)  # Create a logger instance


class PrintServer:

    def __init__(self, cups_server, odoo_server):
        self.cups_server = cups_server
        self.printer_list = False
        self.get_printer_list()
        self.odoo = odoo_server
        logger.info('PrintServer initialized')

    def get_cups_connection(self):
        return self.cups_server._open_connection()

    def get_printer_list(self):
        logger.info('Requested printer list')
        if self.printer_list:
            return self.printer_list
        self.printer_list = self.cups_server.get_printers()
        return self.printer_list

    def print_document(self, job, data, raw=False, options={}):
        logger.info(f'Started: JOB {job.id} Printing document on {job.printer_name} Raw ? {job.raw}')
        printer_name = job.printer_name
        self.get_printer_list()
        printers = self.printer_list or {}
        printer = printers.get(printer_name)

        if printer:
            try:
                if raw:
                    options['raw'] = 'true'
                printer.set_options(options)
                printer.print_document(data)
                logger.info(f'Ended: JOB {job.id} Printing document on {printer_name} Raw ? {job.raw}')
                return {"success": True, "error": False}
            except Exception as e:
                logger.warning(f'Ended: JOB {job.id} Error {e}')
                return {"success": False, "error": str(e)}
        logger.warning(f'Ended: JOB {job.id} Invalid or missing printer name - {printer_name}')
        return {"success": False, "error": True}

    def sync_server_jobs(self, username, active_servers=[]):
        logger.warning(f'Started: Job Sync Scheduler')
        try:
            res = self._sync_server_job(username, active_servers)
            logger.warning(f'Ended: Job Sync Scheduler processed {len(res)} Jobs')
            return res
        except Exception as e:
            logger.warning(f'Ended: Job Sync Scheduler Error {e}')

    def _sync_server_job(self, username, active_servers=[]):
        jobs = self.odoo.search(PRINT_SERVER_JOB,
                                domain=[['server_code', 'in', active_servers],
                                        ['job_state', '=', 'pending']],
                                fields=['job_type',
                                        'printer_id', 'printer_name', 'raw',
                                        'server_id', 'server_code',
                                        'data',
                                        'report_id',
                                        'report_type',
                                        'attachment_id',
                                        'res_ids',
                                        'res_model',
                                        'create_date'
                                        ])
        print("User ", username, " Jobs ", jobs, " Server Code ", active_servers)
        print("odoo ", self.odoo.url, self.odoo.username)
        jobs_list = [self.process_job(job_data) for job_data in jobs]
        return jobs_list

    def process_job(self, job_data):
        job = self.validate_job(job_data)
        error = False
        print("Job data ", job_data)
        if not job or job.state == 'done':
            logger.warning(f'Processing Job: Job {job_data.get("id")} is invalid ignoring')
            error = f"Job {job_data.get('id')} is invalid or already processed {job.state if job else 'Job is Empty'} "

        else:
            job_type = job.job_type
            if job_type == 'authenticate':
                self.process_authentication(job)
            elif job_type == 'fetch_printers':
                error = self.sync_printers(job)
            elif job_type == 'zpl':
                self.process_zpl(job)
            elif job_type == 'reset_printer':
                self.reset_printer(job)
            elif job_type == 'report':
                self.process_report(job)
            else:
                error = f"Invalid Job Type {job_type}"

        print("JOB ", job)
        print("Error ", error)
        if error:
            self.mark_job_failed(job, error, job_data=job_data)
        else:
            self.mark_job_done(job)
        return job

    def process_authentication(self, job):
        f"""
            Does not require implementation 
            If the job is received this means it part of the pair server 
            and must be confirmed
        """
        return

    def sync_printers(self, job):
        """
            @warning
            ====================================
            Do not expose printer data directly,
            it contains cups server credentials
        """
        try:
            logger.info(f"Job Sync Printers: {job.id} Started")
            printers_data = self.get_printer_list()
            printer_vals = {}
            for printer_name, printer in printers_data.items():
                printer_vals[printer_name] = printer.get_vals()
            print("Printers list ", printer_vals)
            self.odoo.call(PRINT_SERVER, "sync_printers",
                           id=None,
                           args={'data': {'server_code': job.server_code,
                                          'printers': printer_vals}})
            logger.info(f"Job Sync Printers: {job.id} Printers synced  {len(printer_vals.keys())}")
            return False
        except Exception as e:
            logger.warning(f"Job Sync Printer: {job.id} Error {e}")
            return e

    def process_zpl(self, job):
        if job.job_type == 'zpl':
            if job.raw:
                return self.print_zpl(job)
            else:
                return self.print_zpl_image(job)

    def print_zpl(self, job):
        logger.info(f"Job Process ZPL: {job.id} Started")
        try:
            self.print_document(job, base64.b64decode(job.data, validate=True))
            logger.info(f"Job Process ZPL: {job.id} Ended")
            return False
        except Exception as e:
            logger.warning(f"Job Process ZPL: Error {e}")
            return e

    def image_to_pdf_bytes(self, image_path):
        image = Image.open(image_path)
        pdf_bytes = io.BytesIO()
        image.convert("RGB").save(pdf_bytes, format="PDF")
        return pdf_bytes.getvalue()

    def print_zpl_image(self, job):
        logger.info(f"Job Process Image: {job.id} Started")
        url = "http://api.labelary.com/v1/printers/8dpmm/labels/2.872x4.30/0/"
        headers = {"Accept": "image/png"}  # Request a PNG response
        response = requests.post(url, headers=headers, data=job.data.encode("utf-8"), stream=True)
        if response.status_code == 200:
            try:
                self.print_document(job, response.content)
                logger.info(f"Job Process Image: {job.id} Ended")
                return False
            except Exception as e:
                logger.warning(f"Job Process Image: Error {e}")
                error = str(e)
        else:
            error = "Could not convert label data to image"
        return error

    def print_to_ip(self, job):
        port = 9100
        ip = '192.168.1.55'
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((ip, port))
                s.sendall(job.data.encode('utf-8'))
                s.close()
        except Exception as e:
            print(f"\nError sending ZPL to printer: {e}\n")
            return e

    def process_report(self, job):
        """
            The method handles odoo report data e.g. pdf
        """
        logger.info(f"Job Process Report: {job.id} Started")
        data = base64.b64decode(job.data.encode('utf-8'))
        try:
            self.print_document(job, data)
        except Exception as e:
            logger.info(f"Job Process Report: {job.id} Error {e}")
            return e

    def reset_printer(self, job):
        logger.info(f"Job Reset Printer: {job.id} Started")
        self.get_printer_list()
        data = job.get("data") or "^XA^FDTEST^FS^XZ"
        try:
            self.print_document(job, data, raw=False)
            self.print_document(job, data, raw=True)
        except Exception as e:
            logger.info(f"Job Reset Printer: {job.id} Error {e}")
            return e

    def validate_job(self, job_data):
        if not job_data.get("id") or not job_data.get("server_code"):
            print("not server id or server code")
            return

        try:
            job = ServerJob.create_job(job_data)
            print("JOb Validated ", job)
            return job
        except Exception as e:
            logger.warning(f"Error Creating Job {e} {job_data}")
            return

    def mark_job_done(self, job, log={}):
        try:
            self.odoo.call(PRINT_SERVER_JOB, 'mark_as_done',
                           id=[job.id],
                           args={'response': log})
        except Exception as e:
            try:
                self.odoo.call(PRINT_SERVER_JOB, 'mark_as_done', id=[job.id], args={'response': str(e)})
            except Exception as e:
                logger.warning(f"Job Mark Job Done: {job.id} Error {e}")
        if job and job.state != 'done':
            job.mark_as_done()

    def mark_job_failed(self, job, error, job_data={}):
        job_id = False
        print("marking as failed ", job, error)
        if not job:
            job_id = job_data.get("id")
        try:
            res = self.odoo.call(PRINT_SERVER_JOB, 'mark_as_done',
                           id=[int(job_id)],
                           args={'response': error})
            print("mark as faild result ", res)
        except Exception as e:
            try:
                print("Exception mark as failed", e)
                self.odoo.call(PRINT_SERVER_JOB, 'mark_as_failed', id=[int(job_id)], args={'response': str(e)})
            except Exception as e:
                print("Exception 2 mark as failed")
                logger.warning(f"Job Mark as Failed: {job_id} Error {e}")

        if job:
            job.mark_as_failed(reason=error)
