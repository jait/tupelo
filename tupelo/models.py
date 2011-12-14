#!/usr/bin/env python
# vim: set sts=4 sw=4 et:


class Manager(object):
    def __init__(self):
        self.objects = []

    def get(self, **kwargs):
        for obj in self.objects:
            match = True
            for key in kwargs:
                if not hasattr(obj, key) or getattr(obj, key) != kwargs[key]:
                    match = False
                    break

            if match:
                return obj

        return None

    def append(self, obj):
        return self.objects.append(obj)

    def remove(self, obj):
        return self.objects.remove(obj)

    def __iter__(self):
        return self.objects.__iter__()
