#!/usr/bin/env python
# vim: set sts=4 sw=4 et:

class Document(object):
    """
    Base class for DAL documents.
    """
    def __init__(self):
        self._data = {}

class BaseField(object):
    """
    Base class for Fields.

    Instances of this class (and its subclasses) can be
    attached to Document instances.
    """
    def __init__(self, allow_none=True):
        self.allow_none = allow_none

    def __get__(self, instance, owner):
        if instance is None:
            return self

        try:        
            return instance._data[id(self)]
        except (AttributeError, KeyError):
            return None

    def __set__(self, instance, value):
        if value is None:
            if not self.allow_none:
                raise TypeError("'None' is not allowed")
        else:
            self.validate(value)

        instance._data[id(self)] = value

    def validate(self, value):
        """
        Validate the value for the field, if applicable.
        """
        pass


class StringField(BaseField):
    def validate(self, value):
        if not isinstance(value, basestring):
            raise TypeError('Value must be a string')

class ResultSet(list):
    pass

class Manager(object):
    def __init__(self):
        self.objects = []

    def all(self):
        return ResultSet(self.objects)

    def _filter(self, kwargs, limit=0):
        result = ResultSet()
        nresult = 0
        for obj in self.objects:
            match = True
            for key in kwargs:
                if not hasattr(obj, key) or getattr(obj, key) != kwargs[key]:
                    match = False
                    break

            if match:
                result.append(obj)
                if limit > 0:
                    nresult += 1
                    if nresult == limit:
                        return result

        return result

    def get(self, **kwargs):
        """
        Get exactly one object mathing the query.

        Return None if there are no matches.
        """
        result = self._filter(kwargs, 1)
        if len(result) == 1:
            return result[0]

        return None

    def filter(self, **kwargs):
        """
        Get all objects that match the query.

        Returns a list.
        """
        return self._filter(kwargs)

    def append(self, obj):
        """
        Append an object to the store.
        """
        return self.objects.append(obj)

    def remove(self, obj):
        """
        Remove a certain object from the store.
        """
        return self.objects.remove(obj)

    def __iter__(self):
        """
        Return an iterator for all objects in the data store.
        """
        return self.all().__iter__()
