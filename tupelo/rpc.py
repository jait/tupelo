#!/usr/bin/env python
# vim: set sts=4 sw=4 et:

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

def _memoize(f, cache={}):
    def g(*args, **kwargs):
        key = (f, tuple(args), frozenset(kwargs.items()))
        if key not in cache:
            cache[key] = f(*args, **kwargs)
        return cache[key]
    return g

def _itersubclasses(cls, _seen=None):
    """
    itersubclasses(cls)

    Generator over all subclasses of a given class, in depth first order.
    """
    if not isinstance(cls, type):
        raise TypeError('itersubclasses must be called with '
                        'new-style classes, not %.100r' % cls)
    if _seen is None: _seen = set()
    try:
        subs = cls.__subclasses__()
    except TypeError: # fails only when cls is type
        subs = cls.__subclasses__(cls)
    for sub in subs:
        if sub not in _seen:
            _seen.add(sub)
            yield sub
            for sub in _itersubclasses(sub, _seen):
                yield sub

class RPCSerializable(object):
    """
    Base class for objects that are serializable into
    an RPC-safe form.
    """
    def __eq__(self, other):
        if not hasattr(self, 'rpc_attrs'):
            return object.__eq__(self, other)

        if hasattr(self, 'rpc_type'):
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
        iterator = iter(cls.rpc_attrs)
        while 1:
            data = iterator.next().split(':')
            if len(data) == 1:
                data.append(None)
            yield (data[0], data[1])

    def rpc_encode(self):
        """
        Encode an instance of RPCSerializable into an rpc object.
        """
        if hasattr(self, 'rpc_attrs'):
            rpcobj = {}
            for attr, _ in self.iter_rpc_attrs():
                rpcform = None
                try:
                    rpcform = getattr(self, attr)
                    rpcform = rpc_encode(rpcform)
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
        if hasattr(cls, 'rpc_attrs'):
            instance = cls()
            for attr, atype in cls.iter_rpc_attrs():
                if rpcobj.has_key(attr):
                    attr_cls = cls.get_class_for_type(atype)
                    if attr_cls:
                        setattr(instance, attr,
                                rpc_decode(attr_cls, rpcobj[attr]))
                    else:
                        setattr(instance, attr, rpcobj[attr])

            return instance
        else:
            return rpcobj

    @classmethod
    def rpc_decode(cls, rpcobj):
        """
        Decode an rpc object into an instance of cls.
        """
        return cls.rpc_decode_simple(rpcobj)

    @classmethod
    @_memoize
    def get_class_for_type(cls, type):
        if type is None:
            return None

        # try first if some class has a overridden type
        for sub in _itersubclasses(cls):
            if hasattr(sub, 'rpc_type') and sub.rpc_type == type:
                return sub
        # then try with class name
        for sub in _itersubclasses(cls):
            if sub.__name__ == type:
                return sub

        return None

