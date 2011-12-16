#!/usr/bin/env python
# vim: set sts=4 sw=4 et:


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
        result = self._filter(kwargs, 1)
        if len(result) == 1:
            return result[0]

        return None

    def filter(self, **kwargs):
        return self._filter(kwargs)

    def append(self, obj):
        return self.objects.append(obj)

    def remove(self, obj):
        return self.objects.remove(obj)

    def __iter__(self):
        return self.all().__iter__()
