from requests import Session


class Requestor(Session):

    def __init__(self, prefix, *args, **kwargs):
        super(Requestor, self).__init__(*args, **kwargs)
        self.prefix = prefix

    def get(self, path, *args, **kwargs):
        url = self.build_url(path)
        return super(Requestor, self).get(url, *args, **kwargs)

    def post(self, path, *args, **kwargs):
        url = self.build_url(path)
        return super(Requestor, self).post(url, *args, **kwargs)

    def put(self, path, *args, **kwargs):
        url = self.build_url(path)
        return super(Requestor, self).put(url, *args, **kwargs) 

    def delete(self, path, *args, **kwargs):
        url = self.build_url(path)
        return super(Requestor, self).delete(url, *args, **kwargs) 

    def build_url(self, path):
        if path.startswith('/'):
            path = path[1:]

        if self.prefix.endswith('/'):
            return '%s%s' % (self.prefix, path)

        return '%s/%s' % (self.prefix, path)
