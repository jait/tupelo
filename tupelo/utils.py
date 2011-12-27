#!/usr/bin/env python
# vim: set sts=4 sw=4 et:

import uuid
import base64
from functools import wraps


def itersubclasses(cls, _seen=None):
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
            for sub in itersubclasses(sub, _seen):
                yield sub

def simple_decorator(decorator):
    """This decorator can be used to turn simple functions
    into well-behaved decorators, so long as the decorators
    are fairly simple. If a decorator expects a function and
    returns a function (no descriptors), and if it doesn't
    modify function attributes or docstring, then it is
    eligible to use this. Simply apply @simple_decorator to
    your decorator and it will automatically preserve the
    docstring and function attributes of functions to which
    it is applied."""
    def new_decorator(func):
        decf = decorator(func)
        decf.__name__ = func.__name__
        decf.__doc__ = func.__doc__
        decf.__dict__.update(func.__dict__)
        return decf
    # Now a few lines needed to make simple_decorator itself
    # be a well-behaved decorator.
    new_decorator.__name__ = decorator.__name__
    new_decorator.__doc__ = decorator.__doc__
    new_decorator.__dict__.update(decorator.__dict__)
    return new_decorator

@simple_decorator
def traced(func):
    """
    A decorator for tracing func calls.
    """
    def wrapper(*args, **kwargs):
        print "DEBUG: entering %s()" % func.__name__
        retval = func(*args, **kwargs)
        return retval

    return wrapper

def synchronized_method(lock_name):
    """
    Simple synchronization decorator for methods.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            lock = self.__getattribute__(lock_name)
            lock.acquire()
            try:
                return func(self, *args, **kwargs)
            finally:
                lock.release()

        return wrapper

    return decorator

def short_uuid():
    """
    Generate a short, random unique ID.

    Returns a string (base64 encoded UUID).
    """
    return base64.urlsafe_b64encode(uuid.uuid4().get_bytes()).replace('=', '')

