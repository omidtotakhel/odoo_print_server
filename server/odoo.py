import server.client as client


class Odoo:

    def __init__(self, url, db, username, password):

        # Odoo server information
        self.url = url
        self.db = db
        self.username = username
        self.password = password

        print(f"Odoo: Connecting to {self.url} DB {self.db} as {self.username} with {self.password}")
        # Connect to the Odoo server using the XML-RPC client
        common_proxy = client.ServerProxy('{}/xmlrpc/2/common'.format(url), allow_none=True)
        self.uid = common_proxy.authenticate(db, username, password, {})
        if self.uid:
            print(f"Connected to {url} database {db} as {username}")
            self.rpc = client.ServerProxy('{}/xmlrpc/2/object'.format(url), allow_none=True)
        else:
            self.rpc = False
            print("Error Connecting to odoo using rpc")

    def search(self, model, domain=False, fields=False, order=False):
        if not self.rpc:
            self._rpc_not_init()
            return
        return self.rpc.execute_kw(self.db, self.uid, self.password,
                                   model, 'search_read', [domain or []], {'fields': fields or ['id'],
                                                                          'order': order})

    def browse(self, model, domain=False):
        if not self.rpc:
            self._rpc_not_init()
            return
        return self.rpc.execute_kw(self.db, self.uid, self.password,
                                   model, 'search', [domain or []])

    def write(self, model, id, vals):
        if not self.rpc:
            self._rpc_not_init()
            return
        return self.rpc.execute_kw(self.db, self.uid, self.password,
                                   model, 'write', [[id], vals])

    def unlink(self, model, id):
        if not self.rpc:
            self._rpc_not_init()
            return
        self.call(model, 'unlink', [id])

    def call(self, model, method, id=False, args=False):
        if not self.rpc:
            self._rpc_not_init()
            return
        params = []
        if id:
            params.append(id)
        if args:
            params.append(args)

        return self.rpc.execute_kw(self.db, self.uid, self.password,
                                   model, method, params)

    def _rpc_not_init(self):
        print("RPC is not initialized")


