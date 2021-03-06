#!/usr/bin/env python
# vim: set sts=4 sw=4 et:

from typing import Union

def rpc_encode(obj):
    """
    Encode an object into RPC-safe form.
    """
    try:
        return obj.rpc_encode()
    except AttributeError:
        return obj

def rpc_decode(cls, rpcobj):
    """
    Decode an RPC-form object into an instance of cls.
    """
    try:
        return cls.rpc_decode(rpcobj)
    except AttributeError:
        return rpcobj

def _memoize(func, cache={}):
    def decf(*args, **kwargs):
        key = (func, tuple(args), frozenset(list(kwargs.items())))
        if key not in cache:
            cache[key] = func(*args, **kwargs)
        return cache[key]
    return decf

def _itersubclasses(cls, _seen=None):
    """
    itersubclasses(cls)

    Generator over all subclasses of a given class, in depth first order.
    """
    if not isinstance(cls, type):
        raise TypeError('itersubclasses must be called with '
                        'new-style classes, not %.100r' % cls)
    if _seen is None:
        _seen = set()
    try:
        subs = cls.__subclasses__()
    except TypeError: # fails only when cls is type
        subs = cls.__subclasses__(cls)
    for sub in subs:
        if sub not in _seen:
            _seen.add(sub)
            yield sub
            for subsub in _itersubclasses(sub, _seen):
                yield subsub

class RPCSerializable():
    """
    Base class for objects that are serializable into
    an RPC-safe form.
    """
    rpc_attrs = None
    rpc_type = None

    def __eq__(self, other):
        if not self.rpc_attrs:
            return super().__eq__(other)

        if self.rpc_type:
            try:
                if self.rpc_type != other.rpc_type:
                    return False
            except AttributeError:
                return False

        for attr, _ in self.iter_rpc_attrs():
            try:
                if getattr(self, attr) != getattr(other, attr):
                    return False
            except AttributeError:
                return False

        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    @classmethod
    def iter_rpc_attrs(cls):
        """
        Generator for iterating rpc_attrs with attr and type separated.
        """
        if not cls.rpc_attrs:
            return

        iterator = iter(cls.rpc_attrs or tuple())
        while 1:
            try:
                data = next(iterator).split(':')
            except StopIteration:
                return

            if len(data) == 1:
                data.append(None)
            yield (data[0], data[1])

    def rpc_encode(self) -> Union[dict, 'RPCSerializable']:
        """
        Encode an instance of RPCSerializable into an rpc object.
        """
        if self.rpc_attrs:
            rpcobj = {}
            for attr, _ in self.iter_rpc_attrs():
                rpcform = None
                try:
                    rpcform = rpc_encode(getattr(self, attr))
                except AttributeError:
                    pass

                if rpcform is not None:
                    rpcobj[attr] = rpcform

            return rpcobj
        # default behaviour
        return self

    @classmethod
    def rpc_decode_simple(cls, rpcobj):
        """
        Default decode method.
        """
        if cls.rpc_attrs:
            instance = cls()
            for attr, atype in cls.iter_rpc_attrs():
                instance.rpc_decode_attr(rpcobj, attr, atype)

            return instance
        else:
            return rpcobj

    @classmethod
    def rpc_decode(cls, rpcobj) -> 'RPCSerializable':
        """
        Decode an rpc object into an instance of cls.
        """
        return cls.rpc_decode_simple(rpcobj)

    def rpc_decode_attr(self, rpcobj: dict, attr: str, atype=None):
        """
        Decode one attribute.
        """
        if attr in rpcobj:
            attr_cls = self.get_class_for_type(atype)
            if attr_cls:
                setattr(self, attr,
                        rpc_decode(attr_cls, rpcobj[attr]))
            else:
                setattr(self, attr, rpcobj[attr])

    @classmethod
    @_memoize
    def get_class_for_type(cls, atype):
        if atype is None:
            return None

        # try first if some class has a overridden type
        for sub in _itersubclasses(RPCSerializable):
            if sub.rpc_type == atype:
                return sub
        # then try with class name
        for sub in _itersubclasses(RPCSerializable):
            if sub.__name__ == atype:
                return sub

        return None

