import six

from .apiobject import ApiObject


class ResourceMeta(type):

    def __new__(cls, name, bases, attrs):
        klass = super(ResourceMeta, cls).__new__(cls, name, bases, attrs)

        cls_name = klass.class_name()
        assert cls_name not in klass._registry
        klass._registry[cls_name] = klass


        return klass


def base(requestor=None):
    attrs = {'_registry': {}}
    klass = ResourceMeta('Base', (Resource,), attrs)

    def bind(cls, requestor):
        klass._requestor = requestor

    klass.bind = classmethod(bind)
    klass.bind(requestor)

    return klass


class Resource(ApiObject):

    TYPE_FIELD = None

    @classmethod
    def class_name(cls):
        return cls.__name__.lower()

    @classmethod
    def class_path(cls):
        return '/%s' % cls.class_name()

    @classmethod
    def retrieve(cls, id, requestor=None, **kwargs):
        instance = cls(id, requestor=requestor, **kwargs)
        instance.refresh()
        return instance

    def __init__(self, id=None, requestor=None, **kwargs):
        super(Resource, self).__init__(**kwargs)

        if requestor:
            self.bind(requestor)

        if id:
            self['id'] = id

    def convert_to_apiobject(self, value):
        if isinstance(value, dict) and self.TYPE_FIELD and \
                self.TYPE_FIELD in value:
            klass = self._registry[value[self.TYPE_FIELD]]
            return klass(**value)
        else:
            return value

    def refresh(self, requestor=None):
        if requestor:
            self.bind(requestor)

        response = self._requestor.get(self.instance_path(), headers=self.get_headers())
        if not response:
            self.raise_for_response(response)

        self.refresh_from(self.data_from_response(response))
        return self

    @classmethod
    def raise_for_response(cls, response):
        response.raise_for_status()

    def data_from_response(self, response):
        return response.json()

    def refresh_from(self, values, partial=False, last_response=None, requestor=None):
        super(Resource, self).refresh_from(values, partial=partial, last_response=last_response)

    def set_values(self, values):
        # XXX: Use some kind of registry to populate child objects
        super(Resource, self).set_values(values)

    def get_id(self):
        return self.id

    @classmethod
    def get_headers(cls):
        return {}

    def instance_path(self):
        return '%s/%s' % (self.class_path(), self.get_id())


class CreatableResourceMixin(object):

    @classmethod
    def create(cls, requestor=None, **params):
        requestor = requestor or getattr(cls, '_requestor', None)
        assert requestor

        headers = cls.get_headers()
        response = requestor.post(cls.class_path(), headers=headers, json=params)
        cls.raise_for_response(response)

        instance = cls()
        instance.refresh_from(response.json())

        return instance


class UpdatableResourceMixin(object):

    def update_request(self, requstor, path, *args, **kwargs):
        return requestor.put(path, *args, **kwargs)

    def save(self, requestor=None):
        updated_params = self.prepare(None)
        assert updated_params

        if requestor:
            self.bind(requestor)

        response = self.update_request(self.instance_path(), json=updated_params)
        self.raise_for_response(response)

        self.refresh_from(response.json())
        return self


class DeletableResourceMixin(object):

    def delete_request(self, requestor, path):
        return requestor.delete(path)

    def delete(self, requestor=None):
        if requestor:
            self.bind(requestor)

        response = self.delete_request(self._requestor, self.instance_path())
        self.raise_for_response(response)
