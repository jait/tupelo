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

class RPCSerializable(object):
    """
    Base class for objects that are serializable into
    an RPC-safe form.
    """
    def rpc_encode(self):
        """
        Encode an instance of RPCSerializable into an rpc object.
        """
        if hasattr(self, 'rpc_fields'):
            rpcobj = {}
            for field in self.rpc_fields:
                rpcform = None
                try:
                    rpcform = getattr(self, field)
                    rpcform = rpc_encode(rpcform)
                except AttributeError:
                    pass

                if rpcform is not None:
                    rpcobj[field] = rpcform
            return rpcobj
        # default behaviour
        return self
    
    @classmethod
    def rpc_decode_simple(cls, rpcobj):
        """
        Default decode method.
        """
        if hasattr(cls, 'rpc_fields'):
            instance = cls()
            for attr in cls.rpc_fields:
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

