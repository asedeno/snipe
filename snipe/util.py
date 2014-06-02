# -*- encoding: utf-8 -*-
# Copyright © 2014 Karl Ramm
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above
# copyright notice, this list of conditions and the following
# disclaimer in the documentation and/or other materials provided
# with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
# CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
# INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
# TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR
# TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF
# THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
# SUCH DAMAGE.


'''
Assorted utility functions.
'''


import logging


class SnipeException(Exception):
    pass


class Configurable:
    registry = {}

    def __init__(self, key, default=None, doc=None, action=None):
        self.key = key
        self.default = default
        self._action = action
        self.doc = doc
        self.registry[key] = self

    def __get__(self, instance, owner):
        return instance.context.conf.get('set', {}).get(self.key, self.default)

    def __set__(self, instance, value):
        instance.context.conf.setdefault('set', {})[self.key] = value
        self.action(instance, value)

    def action(self, instance, value):
        if self._action is not None:
            self._action(instance.context, value)

    @classmethod
    def immanentize(self, context):
        for configurable in self.registry.values():
            configurable.action(context, configurable.default)


class Level(Configurable):
    def __init__(self, key, logger, default=logging.WARNING, doc=None):
        super().__init__(key, default, doc=doc)
        self.logger = logger

    def action(self, instance, value):
        logging.getLogger(self.logger).setLevel(value)


# these don't need to actually be properties anywhere
logging_properties = [
    Level(
        userspace_name,
        program_name,
        {'log.context': logging.INFO}.get(userspace_name, logging.WARNING),
        'logging for %s object' % (program_name,)
        )
    for userspace_name, program_name in [
        ('log.context', 'Snipe'),
        ('log.roost.engine', 'Rooster'),
        ('log.roost', 'Roost'),
        ('log.ttyfrontend', 'TTYFrontend'),
        ('log.ttyrender', 'TTYRender'),
        ('log.curses', 'TTYRender.curses'),
        ('log.messager', 'Messager'),
        ('log.editor', 'Editor'),
        ('log.asyncio', 'asyncio'),
        ]]
