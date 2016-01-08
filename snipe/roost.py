# -*- encoding: utf-8 -*-
# Copyright © 2014 the Snipe contributors
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
snipe.roost
-----------
Backend for talking to `roost <https://github.com/roost-im>`_
'''

_backend = 'Roost'


import asyncio
import collections
import itertools
import time
import shlex
import os
import urllib.parse
import contextlib
import re
import pwd
import math
import getopt
import traceback
import codecs
import subprocess

from . import messages
from . import _rooster
from . import util
from . import filters
from . import keymap
from . import interactive


class Roost(messages.SnipeBackend):
    name = 'roost'

    backfill_count = util.Configurable(
        'roost.backfill_count', 8,
        'Keep backfilling until you have this many messages'
        ' unless you hit the time limit',
        coerce=int)
    backfill_length = util.Configurable(
        'roost.backfill_length', 24 * 3600,
        'only backfill this far looking for roost.backfill_count messages',
        coerce=int)
    url = util.Configurable(
        'roost.url', 'https://roost-api.mit.edu')
    service_name = util.Configurable(
        'roost.servicename', 'HTTP',
        "Kerberos servicename, you probably don't need to change this")
    realm = util.Configurable(
        'roost.realm', 'ATHENA.MIT.EDU',
        'Zephyr realm that roost is fronting for')
    signature = util.Configurable(
        'roost.signature', pwd.getpwuid(os.getuid()).pw_gecos.split(',')[0],
        'Name-ish field on messages')
    subunify = util.Configurable(
        'roost.subunify', False, 'un-ify subscriptions')
    indent = util.Configurable(
        'roost.barnowl_indent_body_string', '',
        'Indent message bodies with this string (barnowl expats may '
        'wish to set it to eight spaces)')

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.messages = []
        self.r = _rooster.Rooster(self.url, self.service_name)
        self.chunksize = 128
        self.loaded = False
        self.backfilling = False
        self.new_task = asyncio.async(self.error_message(
            'getting new messages', self.r.newmessages, self.new_message))
        self.tasks.append(self.new_task)

    @asyncio.coroutine
    def error_message(self, activity, func, *args):
        """run a coroutine, creating a message with a traceback if it raises"""
        try:
            return (yield from func(*args))
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.log.exception(activity)
            msg = RoostErrorMessage(self, activity, e, traceback.format_exc())
            self.messages.append(msg)
            self.drop_cache()
            self.redisplay(msg, msg)

    @property
    def principal(self):
        return self.r.principal

    @asyncio.coroutine
    def send(self, paramstr, body):
        self.log.debug('send paramstr=%s', paramstr)

        flags, recipients = getopt.getopt(shlex.split(paramstr), 'xRCc:i:O:')

        flags = dict(flags)
        self.log.debug('send flags=%s', repr(flags))

        if not recipients:
            recipients=['']

        if '-C' in flags and len(recipients) > 1:
            body = 'CC: ' + ' '.join(recipients) + '\n' + body

        if '-R' in flags:
            body = codecs.encode(body, 'rot13')

        for recipient in recipients:
            if '-x' in flags:
                flags['-O'] = 'crypt'
                cmd = ['zcrypt', '-E', '-c', flags.get('-c', 'MESSAGE')]
                proc = yield from asyncio.create_subprocess_exec(
                    *cmd,
                    **dict(
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        )
                    )
                stdout, stderr = yield from proc.communicate(body.encode())
                stdout = stdout.decode(errors='replace')
                stderr = stderr.decode(errors='replace')
                if proc.returncode:
                    self.log.error(
                        'roost: %s returned %d',
                        ' '.join(cmd), proc.returncode)
                if stderr:
                    self.log.error(
                        'roost: %s send %s to stderr',
                        ' '.join(cmd), repr(stderr))
                    raise Exception('zcrypt: ' + stderr)
                if proc.returncode:
                    raise Exception('zcrypt returned %d' % (proc.returncode))
                body = stdout

            message = {
                'class': flags.get('-c', 'MESSAGE'),
                'instance': flags.get('-i', 'PERSONAL'),
                'recipient': recipient,
                'opcode': flags.get('-O', ''),
                'signature': flags.get('-s', self.signature),
                'message': body,
                }

            self.log.debug('sending %s', repr(message))

            result = yield from self.r.send(message)
            self.log.info('sent to %s: %s', recipient, repr(result))

    @asyncio.coroutine
    def new_message(self, m):
        msg = yield from self.construct_and_maybe_decrypt(m)
        if self.messages and msg.time <= self.messages[-1].time:
            msg.time = self.messages[-1].time + .00001
        self.messages.append(msg)
        self.drop_cache()
        self.redisplay(msg, msg)

    @asyncio.coroutine
    def construct_and_maybe_decrypt(self, m):
        msg = RoostMessage(self, m)
        try:
            if msg.data.get('opcode') == 'crypt':
                cmd = ['zcrypt', '-D', '-c', msg.data['class']]
                proc = yield from asyncio.create_subprocess_exec(
                    *cmd,
                    **dict(
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        )
                    )
                stdout, stderr = yield from proc.communicate(msg.body.encode())
                stdout = stdout.decode(errors='replace')
                stderr = stderr.decode(errors='replace')
                if proc.returncode:
                    self.log.error(
                        'roost: %s returned %d', ' '.join(cmd), proc.returncode)
                if stderr:
                    self.log.error(
                        'roost: %s send %s to stderr',
                        ' '.join(cmd), repr(stderr))
                if not (proc.returncode or stderr):
                    sigil = '**END**\n'
                    if stdout.endswith(sigil):
                        stdout = stdout[:-len(sigil)]
                    msg.transform('zcrypt', stdout)
        except:
            self.log.exception('zcrypt, decrypting')
        return msg

    def backfill(self, mfilter, target=None, count=0, origin=None):
        self.log.debug(
            'backfill([filter], target=%s, count=%s, origin=%s)',
            util.timestr(target), count, util.timestr(origin))

        # if we're not gettting new messages, don't try to get old ones
        if self.loaded or self.new_task.done() or target is None:
            return

        filledpoint = self.messages[0].time if self.messages else time.time()

        if filledpoint < target:
            self.log.debug(
                '%s < %s', util.timestr(filledpoint), util.timestr(target))
            return

        target = max(target, filledpoint - self.backfill_length)

        self.log.debug('triggering backfill, target=%s', util.timestr(target))

        msgid = None
        if self.messages:
            msgid = self.messages[0].data.get('id')
            if origin is None:
                origin = filledpoint

        self.reap_tasks()
        self.tasks.append(
            asyncio.async(self.error_message(
                'backfilling',
                self.do_backfill, msgid, mfilter, target, count, origin)))

    @asyncio.coroutine
    def do_backfill(self, start, mfilter, target, count, origin):
        #yield from asyncio.sleep(.0001)
        self.log.debug(
            'do_backfill(start=%s, [filter], %s, %s, origin=%s)',
            repr(start), util.timestr(target), repr(count), util.timestr(origin))

        @contextlib.contextmanager
        def backfillguard():
            if self.backfilling:
                yield True
            else:
                self.log.debug('entering guard')
                self.backfilling = True
                yield False
                self.backfilling = False
                self.log.debug('leaving guard')

        with backfillguard() as already:
            if already:
                self.log.debug('already backfiling')
                return

            if mfilter is None:
                mfilter = lambda m: True

            if self.loaded:
                self.log.debug('no more messages to backfill')
                return
            self.log.debug('backfilling')
            chunk = yield from self.r.messages(start, self.chunksize)

            if chunk['isDone']:
                self.log.info('IT IS DONE.')
                self.loaded = True
            ms = []
            for m in chunk['messages']:
                cm = yield from self.construct_and_maybe_decrypt(m)
                ms.append(cm)
            count += len([m for m in ms if mfilter(m)])
            # Make sure ordering is stable
            # XXX really assuming messages are millisecond unique si dumb
            anchor = []
            if self.messages and ms:
                anchor = [(self.messages[0], ms[0])]
            for (nextmsg, prevmsg) in itertools.chain(anchor, zip(ms, ms[1:])):
                # walking backwards through time
                if nextmsg.time == prevmsg.time:
                    prevmsg.time = nextmsg.time - .00001
            ms.reverse()
            self.messages = ms + self.messages
            self.drop_cache()
            self.log.warning(
                '%d messages, total %d, earliest %s',
                 count, len(self.messages), util.timestr(self.messages[0].time))

            # and (maybe) circle around
            yield from asyncio.sleep(.1)
            self.backfill(mfilter, target, count=count, origin=origin)

            self.redisplay(ms[0], ms[-1])
            self.log.debug('done backfilling')

    @keymap.bind('R S')
    def dump_subscriptions(self, window: interactive.window):
        subs = yield from self.r.subscriptions()
        subs = [(x['class'], x['instance'], x['recipient'] or '*') for x in subs]
        subs.sort()
        subs = [' '.join(x) for x in subs]
        window.show('\n'.join(subs))

    @staticmethod
    def spec_to_triplets(params):
        flags, rest = getopt.getopt(shlex.split(params.strip()), 'c:i:r:')
        flags = dict(flags)

        instance = flags.get('-i', '*')
        realm = flags.get('-r', '')
        if realm and not realm.startswith('@'):
            realm = '@' + realm

        if '-c' in flags or not rest:
            class_ = flags.get('-c', 'MESSAGE')
            recipients = rest

            return [(class_, instance, rec + realm) for rec in recipients]
        else:
            return [(class_, instance, realm) for class_ in rest]

    @asyncio.coroutine
    def load_subs(self, filename):
        if not os.path.exists(filename):
            return
        with open(filename) as fp:
            lines = fp.read().split()
        triplets = [line.split(',', 2) for line in lines]

        for triplet in triplets:
            if triplet[2].endswith('@' + self.realm) and triplet[2][0] in '@*':
                triplet[2] = '*'

        yield from self.r.subscribe(triplets)

    @staticmethod
    @util.listify
    def do_subunify(subs):
        for (class_, instance, recipient) in subs:
            for (i, j) in itertools.product(range(4), range(4)):
                yield ('un' * i + class_ + '.d' * j, instance, recipient)

    @keymap.bind('R s')
    def subscribe(self, window: interactive.window):
        spec = yield from window.read_string(
            'subscribe to: ',
            name='zephyr class',
            )
        if spec.strip():
            subs = self.spec_to_triplets(spec)
            if self.subunify:
                subs = self.do_subunify(subs)
            self.log.debug('subbing to %s', repr(subs))
            yield from self.r.subscribe(subs)

    @keymap.bind('R l')
    def subscribe_file(self, window: interactive.window):
        default = os.path.expanduser('~/.zephyr.subs')
        if not os.path.exists(default):
            default = None
        filename = yield from window.read_filename(
            'Load subscriptions from file: ', content=default)
        yield from self.load_subs(filename)

    @keymap.bind('R u')
    def unsubscribe(self, window: interactive.window):
        spec = yield from window.read_string(
            'unsubscribe from: ',
            name='zephyr class',
            )
        if spec.strip():
            subs = self.spec_to_triplets(spec)
            if self.subunify:
                subs = self.do_subunify(subs)
            self.log.debug('unsubbing from %s', repr(subs))
            yield from self.r.unsubscribe(subs)


class RoostMessage(messages.SnipeMessage):
    def __init__(self, backend, m):
        super().__init__(backend, m['message'], m['receiveTime'] / 1000)
        self.data = m
        self._sender = RoostPrincipal(backend, m['sender'])

        self.personal = self.data['recipient'] \
          and self.data['recipient'][0] != '@'
        self.outgoing = self.data['sender'] == self.backend.r.principal

    def __str__(self):
        return (
            'Class: {class_} Instance: {instance} Recipient: {recipient}'
            '{opcode}\n'
            'From: {signature} <{sender}> at {date}\n'
            '{body}\n').format(
            class_=self.data['class'],
            instance=self.data['instance'],
            recipient=self.data['recipient'],
            opcode=(
                ''
                if not self.data['opcode']
                else ' [{}]'.format(self.data['opcode'])),
            signature=self.data['signature'],
            sender=self.sender,
            date=time.ctime(self.data['time'] / 1000),
            body=self.body + \
                ('' if self.body and self.body[-1] == '\n' else '\n'),
            )

    def display(self, decoration):
        tags = self.decotags(decoration)
        instance = self.data['instance']
        instance = instance or "''"
        chunk = []

        if self.personal:
            if self.outgoing:
                #chunk += [(tags + ('bold',), '\N{BLACK RIGHTWARDS ARROWHEAD} ')]
                # the above looks cooler but is not in the ubuntu font
                # constellation for 6x13
                chunk += [(tags + ('bold',), '\N{RIGHTWARDS ARROW} ')]
                chunk += [(tags + ('bold',), self.field('recipient'))]
                chunk.append((tags, ' '))
            else:
                chunk += [(tags + ('bold',), '(personal) ')]

        if not self.personal or self.data['class'].lower() != 'message':
            chunk += [
                (tags, '-c '),
                (tags + ('bold',), self.data['class']),
                ]
        if instance.lower() != 'personal':
            chunk += [
                (tags, ' -i ' + instance),
                ]

        if self.data['recipient'] and self.data['recipient'][0] == '@':
            chunk += [(tags + ('bold',), ' ' + self.data['recipient'])]

        if self.data['opcode']:
            chunk += [(tags, ' [' + self.data['opcode'] + ']')]

        chunk += [
            (tags, ' <' ),
            (tags + ('bold',), self.field('sender')),
            (tags, '>'),
            ]

        sig = self.data.get('signature', '').strip()
        if sig:
            sigl = sig.split('\n')
            sig = '\n'.join(sigl[:1] + ['    ' + s for s in sigl[1:]])
            chunk += [
                (tags, ' ' + sig),
                ]

        chunk.append(
            (tags + ('right',),
             time.strftime(
                ' %H:%M:%S', time.localtime(self.data['time'] / 1000))))

        body = self.body
        body = '\n'.join(self.backend.indent + line for line in body.split('\n'))
        if body:
            if not body.endswith('\n'):
                body += '\n'
            chunk += [(tags, body)]

        return chunk

    class_un = re.compile(r'^(un)*')
    class_dotd = re.compile(r'(\.d)*$')
    def canon(self, field, value):
        if field == 'sender':
            value = str(value)
            atrealmlen = len(self.backend.realm) + 1
            if value[-atrealmlen:] == '@' + self.backend.realm:
                return value[:-atrealmlen]
        elif field == 'class':
            value = value.lower() #XXX do proper unicode thing
            x1, x2 = self.class_un.search(value).span()
            value = value[x2:]
            x1, x2 = self.class_dotd.search(value).span()
            value = value[:x1]
        elif field == 'instance':
            value = value.lower() #XXX do proper unicode thing
            x1, x2 = self.class_dotd.search(value).span()
            value = value[:x1]
        elif field == 'opcode':
            value = value.lower().strip()
        return value

    def reply(self):
        l = []
        if self.transformed == 'rot13':
            l += ['-R']
        if self.data['recipient'] and self.data['recipient'][0] != '@':
            if self.data['class'].upper() != 'MESSAGE':
                l += ['-c', self.data['class']]
            if self.data['instance'].upper() != 'PERSONAL':
                l += ['-i', self.data['instance']]
        if self.outgoing and self.data['recipient']:
            l.append(self.data['recipient'])
        else:
            l.append(self.sender.short())

        return self.backend.name + '; ' + ' '.join(shlex.quote(s) for s in l)

    def followup(self):
        l = []
        if self.transformed == 'rot13':
            l += ['-R']
        if self.transformed == 'zcrypt':
            l += ['-x']
        if self.data['recipient'] and self.data['recipient'][0] != '@':
            if not self.body.startswith('CC: '):
                return self.reply()
            else:
                cc = self.body.splitlines()[0].split()[1:]
                cc.append(self.sender.short())
                cc = [self.canon('sender', x) for x in cc] # canonicalize
                me = self.canon('sender', self.backend.r.principal)
                cc = list(set(cc) - {me}) # uniquify, filter self
                l += ['-C'] + cc
        if self.data['class'].upper() != 'MESSAGE':
            l += ['-c', self.data['class']]
        if self.data['instance'].upper() != 'PERSONAL':
            l += ['-i', self.data['instance']]
        if self.data['recipient'] and self.data['recipient'][0] == '@':
            l += [self.data['recipient']] # presumably a there should be a -r?
        return self.backend.name + '; ' + ' '.join(shlex.quote(s) for s in l)

    def filter(self, specificity=0):
        nfilter = filters.Compare('==', 'backend', self.backend.name)
        if self.personal:
            if str(self.sender) == self.backend.principal:
                conversant = self.field('recipient')
            else:
                conversant = self.field('sender')
            return filters.And(
                nfilter,
                filters.Truth('personal'),
                filters.Or(
                    filters.Compare('=', 'sender', conversant),
                    filters.Compare('=', 'recipient', conversant)))
        elif self.field('class'):
            nfilter = filters.And(
                nfilter,
                filters.Compare('=', 'class', self.field('class')))
            if specificity > 0:
                nfilter = filters.And(
                    nfilter,
                    filters.Compare('=', 'instance', self.field('instance')))
            if specificity > 1:
                nfilter = filters.And(
                    nfilter,
                    filters.Compare('=', 'sender', self.field('sender')))
            return nfilter

        return super().filter(specificity)


class RoostErrorMessage(messages.SnipeErrorMessage):
    def __init__(self, backend, activity, exception, tracebackstr):
        body = '%s: %s' % (activity, str(exception))
        if not isinstance(exception, _rooster.RoosterException):
            body += '\n' + tracebackstr
        super().__init__(backend, body)


class RoostPrincipal(messages.SnipeAddress):
    def __init__(self, backend, principal):
        self.principal = principal
        super().__init__(backend, [principal])

    def __str__(self):
        return self.principal

    def short(self):
        atrealmlen = len(self.backend.realm) + 1
        if self.principal[-atrealmlen:] == '@' + self.backend.realm:
            return self.principal[:-atrealmlen]
        return self.principal

    def reply(self):
        return self.backend.name + '; ' + self.short()


class RoostTriplet(messages.SnipeAddress):
    def __init__(self, backend, class_, instance, recipient):
        self.class_ = class_
        self.instance = instance
        self.recipient = recipient
        super().__init__(backend, [class_, instance, recipient])
