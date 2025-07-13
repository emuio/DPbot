
from .DbInitServer import DbInitServer
from .DbAdminServer import DbAdminServer


class DbServer(DbInitServer,DbAdminServer):
    def __init__(self):
        DbInitServer.__init__(self)
        DbAdminServer.__init__(self)

