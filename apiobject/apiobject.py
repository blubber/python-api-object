from __future__ import absolute_import, division

from copy import deepcopy
import datetime
from pprint import pformat

import six


class ApiObject(dict):

    def __init__(self, last_response=None, **params):
        super(ApiObject, self).__init__()

        self._unsaved_values = set()
        self._transient_values = set()
        self._last_response = last_response

        self._retrieve_params = params
        self._previous = None
        self.set_values(params)

    @property
    def last_response(self):
        return self._last_response

    @classmethod
    def construct_from(cls, values, last_response=None):
        instance = cls(last_response=last_response)
        instance.refresh_from(values, last_response=last_response)
        return instance

    def refresh_from(self, values, partial=False, last_response=None):
        self._last_response = \
            last_response or getattr(values, '_last_response', None)

        # Wipe old state before setting new.  This is useful for e.g.
        # updating a customer, where there is no persistent card
        # parameter.  Mark those values which don't persist as transient
        if partial:
            self._unsaved_values = (self._unsaved_values - set(values))
        else:
            removed = set(self.keys()) - set(values)
            self._transient_values = self._transient_values | removed
            self._unsaved_values = set()
            self.clear()

        self._transient_values = self._transient_values - set(values)
        self.set_values(values)

        self._previous = values

    def set_values(self, values):
        for k, v in values.items():
            super(ApiObject, self).__setitem__(k, self.convert_to_apiobject(v, key=k))

    def convert_to_apiobject(self, value, key=None):
        return value

    def ignored_keys(self):
        return []

    def prepare(self, previous):
        params = {}
        unsaved_keys = self._unsaved_values or set()
        previous = previous or self._previous or {}

        for k, v in six.iteritems(self):
            if k in self.ignored_keys() or (isinstance(k, str) and k.startswith('_')):
                continue
            #elif isinstance(v, stripe.api_resources.abstract.APIResource):
            #    continue
            elif hasattr(v, 'prepare'):
                child = v.prepare(previous.get(k, None))
                if child != {}:
                    params[k] = child
            elif k in unsaved_keys:
                params[k] = v

        return params

    def update(self, update_dict):
        for k in update_dict:
            self._unsaved_values.add(k)

        return super(ApiObject, self).update(update_dict)

    def __setattr__(self, k, v):
        if k[0] == '_' or k in self.__dict__:
            return super(ApiObject, self).__setattr__(k, v)

        self[k] = v
        return None

    def __getattr__(self, k):
        if k[0] == '_':
            raise AttributeError(k)

        try:
            return self[k]
        except KeyError as err:
            raise AttributeError(*err.args)

    def __delattr__(self, k):
        if k[0] == '_' or k in self.__dict__:
            return super(ApiObject, self).__delattr__(k)
        else:
            del self[k]

    def __setitem__(self, k, v):
        self._unsaved_values.add(k)
        super(ApiObject, self).__setitem__(k, v)

    def __getitem__(self, k):
        try:
            return super(ApiObject, self).__getitem__(k)
        except KeyError as err:
            if k in self._transient_values:
                raise KeyError(
                    "%r.  HINT: The %r attribute was set in the past."
                    "It was then wiped when refreshing the object with "
                    "the result returned by Stripe's API, probably as a "
                    "result of a save().  The attributes currently "
                    "available on this object are: %s" %
                    (k, k, ', '.join(list(self.keys()))))
            else:
                raise err

    def __delitem__(self, k):
        super(ApiObject, self).__delitem__(k)


    def __repr__(self):
        ident_parts = [type(self).__name__]

        if isinstance(self.get('object'), six.string_types):
            ident_parts.append(self.get('object'))

        if isinstance(self.get('id'), six.string_types):
            ident_parts.append('id=%s' % (self.get('id'),))

        unicode_repr = '<%s at %s> JSON: %s' % (
            ' '.join(ident_parts), hex(id(self)), str(self))

        if six.PY2:
            return unicode_repr.encode('utf-8')
        else:
            return unicode_repr

    def __str__(self):
        return '<%s id=%s>\n%s' % (self.__class__.__name__,
                self.get('id'), pformat(dict(self)))

    # This class overrides __setitem__ to throw exceptions on inputs that it
    # doesn't like. This can cause problems when we try to copy an object
    # wholesale because some data that's returned from the API may not be valid
    # if it was set to be set manually. Here we override the class' copy
    # arguments so that we can bypass these possible exceptions on __setitem__.
    def __copy__(self):
        copied = ApiObject(id=self.get('id'))

        copied._retrieve_params = self._retrieve_params

        for k, v in six.iteritems(self):
            # Call parent's __setitem__ to avoid checks that we've added in the
            # overridden version that can throw exceptions.
            super(ApiObject, copied).__setitem__(k, v)

        return copied

    # This class overrides __setitem__ to throw exceptions on inputs that it
    # doesn't like. This can cause problems when we try to copy an object
    # wholesale because some data that's returned from the API may not be valid
    # if it was set to be set manually. Here we override the class' copy
    # arguments so that we can bypass these possible exceptions on __setitem__.
    def __deepcopy__(self, memo):
        copied = self.__copy__()
        memo[id(self)] = copied

        for k, v in six.iteritems(self):
            # Call parent's __setitem__ to avoid checks that we've added in the
            # overridden version that can throw exceptions.
            super(ApiObject, copied).__setitem__(k, deepcopy(v, memo))

        return copied
