#!/usr/bin/env python
# vim: set sts=4 sw=4 et:

DRIVER = 'ram'

class DriverFactory(object):
    """
    Factory for creating database Driver instances.
    TODO: should Driver be singleton instead of this registry hack?
    """
    _drivers =  {}

    @classmethod
    def get(cls, name=DRIVER):
        if cls._drivers.has_key(name):
            return cls._drivers[name]
        else:
            # TODO: find the Driver subclass with the provided name
            driver = RamDriver()
            cls._drivers[name] = driver
            return driver


class Driver(object):
    """
    Base class for database drivers.
    """
    def get_manager(self, cls):
        """
        Get a Manager object for a Document class.
        """
        kind = cls.__name__
        manager = Manager(kind, self)
        return manager

    def all(self, kind):
        """
        Get all objects of a kind in the store.
        """
        raise NotImplemented()

    def get(self, kind, **kwargs):
        """
        Get exactly one object mathing the query.

        Return None if there are no matches.
        """
        raise NotImplemented()

    def filter(self, kind, **kwargs):
        """
        Get all objects that match the query.

        Returns a list.
        """
        raise NotImplemented()

    def put(self, kind, obj):
        """
        Put (replace or append) and object to the store.
        """
        raise NotImplemented()

    def append(self, kind, obj):
        """
        Append an object to the store.
        """
        raise NotImplemented()

    def remove(self, kind, obj):
        """
        Remove a certain object from the store.
        """
        raise NotImplemented()

    def remove_all(self, kind):
        """
        Remove all objects of the certain kind.
        """
        raise NotImplemented()

    def iterator(self, kind):
        """
        Return an iterator for all objects in the data store.
        """
        raise NotImplemented()


class RamDriver(Driver):
    """
    Driver that uses RAM (process heap) for storage.
    """
    name = 'ram'

    def __init__(self):
        self._objects = {}

    def _get_objects(self, kind):
        if not self._objects.has_key(kind):
            self._objects[kind] = []

        return self._objects[kind]

    def all(self, kind):
        return ResultSet(self._get_objects(kind))

    def _filter(self, kind, kwargs, limit=0):
        result = ResultSet()
        nresults = 0
        for obj in self._get_objects(kind):
            match = True
            for key in kwargs:
                if not hasattr(obj, key) or getattr(obj, key) != kwargs[key]:
                    match = False
                    break

            if match:
                result.append(obj)
                if limit > 0:
                    nresults += 1
                    if nresults == limit:
                        return result

        return result

    def get(self, kind, **kwargs):
        """
        Get exactly one object mathing the query.

        Return None if there are no matches.
        """
        result = self._filter(kind, kwargs, 1)
        if len(result) == 1:
            return result[0]

        return None

    def filter(self, kind, **kwargs):
        """
        Get all objects that match the query.

        Returns a list.
        """
        return self._filter(kind, kwargs)

    def put(self, kind, obj):
        """
        Put (replace or append) and object to the store.
        """
        objects = self._get_objects(kind)
        if not obj in objects:
            return objects.append(obj)
        # nothing to do otherwise

    def append(self, kind, obj):
        """
        Append an object to the store.
        """
        return self._get_objects(kind).append(obj)

    def remove(self, kind, obj):
        """
        Remove a certain object from the store.
        """
        return self._get_objects(kind).remove(obj)

    def remove_all(self, kind):
        """
        Remove all objects of the certain kind.
        """
        del self._get_objects(kind)[:]

    def iterator(self, kind):
        """
        Return an iterator for all objects in the data store.
        """
        return self.all(kind).__iter__()


class ManagerDescriptor(object):
    """
    Descriptor to dynamically get a Manager instance for the
    enclosing class.
    """
    def __get__(self, instance, owner):
        # check if owner class has _manager as its _own_ member
        if not owner.__dict__.has_key('_manager'):
            owner._manager = DriverFactory.get().get_manager(owner)

        return owner._manager


class Document(object):
    """
    Base class for DAL documents.
    """
    objects = ManagerDescriptor()

    def __init__(self):
        self._data = {}

    def save(self):
        return self.objects.put(self)


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


class IntegerField(BaseField):
    def validate(self, value):
        if not isinstance(value, int):
            raise TypeError('Value must be an int')


class ResultSet(list):
    pass


class Manager(object):
    """
    Object manager interface.
    """
    def __init__(self, kind, driver):
        self.kind = kind
        self.driver = driver

    def all(self):
        return self.driver.all(self.kind)

    def get(self, **kwargs):
        """
        Get exactly one object mathing the query.

        Return None if there are no matches.
        """
        return self.driver.get(self.kind, **kwargs)

    def filter(self, **kwargs):
        """
        Get all objects that match the query.

        Returns a ResultSet.
        """
        return self.driver.filter(self.kind, **kwargs)

    def put(self, obj):
        """
        Put (replace or append) and object to the store.
        """
        return self.driver.put(self.kind, obj)

    def append(self, obj):
        """
        Append an object to the store.
        """
        return self.driver.append(self.kind, obj)

    def remove(self, obj):
        """
        Remove a certain object from the store.
        """
        return self.driver.remove(self.kind, obj)

    def remove_all(self):
        """
        Remove all objects.
        """
        return self.driver.remove_all(self.kind)

    def __iter__(self):
        """
        Return an iterator for all objects in the data store.
        """
        return self.driver.iterator(self.kind)

