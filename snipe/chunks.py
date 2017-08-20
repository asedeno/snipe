# -*- encoding: utf-8 -*-
# Copyright © 2017 the Snipe contributors
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
snipe.chunk
----------

Chunk type
'''


import re


class Chunk:
    """Chunk of decorated text going headed for the redisplay.

    Class to replace the ad-hoc representation of chunks as lists and
    tuples ( [(tags, text), (tags, text)] ) with somethign that does a
    bit of validation and gives us a central place to experiment with
    the representation.

    Chunk() -> new empty chunk
    Chunk(iterable) -> new chunk initialized from iterable

    (each item must be a typle with iterable and a string)
    """

    def __init__(self, data=()):
        self.contents = []
        self.extend(data)

    def extend(self, data):
        """extend chunk by appending elements from the iterable"""

        for tags, text in data:
            self.append((tags, text))

    def append(self, chunklet):
        """extend a chunk with one (tags, text) tuple

        tags should be an iterable of strings, and text should be a
        string.
        """

        tags, text = chunklet
        self.contents.append((tuple(tags), str(text)))

    def __getitem__(self, k):
        x = self.contents[k]
        if isinstance(x, list):
            return Chunk(x)
        return x

    def __setitem__(self, k, v):
        if isinstance(v, tuple):
            tags, text = v
            self.contents[k] = (tuple(tags), text)
        else:
            self.contents[k] = list(Chunk(v))

    def __delitem__(self, k):
        del self.contents[k]

    def __len__(self):
        return len(self.contents)

    def __iter__(self):
        for tags, text in self.contents:
            yield tags, text

    def __repr__(self):
        return self.__class__.__name__ + '(' + repr(self.contents) + ')'

    def __str__(self):
        return ''.join(x[1] for x in self.contents)

    def __add__(self, other):
        x = Chunk(self.contents)
        x.extend(other)
        return x

    def __radd__(self, other):
        x = Chunk(other)
        x.extend(self.contents)
        return x

    def __iadd__(self, b):
        self.extend(b)
        return self

    def __eq__(self, other):
        if isinstance(other, Chunk):
            return self.contents == other.contents
        return self.contents == list(other)

    def mark_re(self, regexp, mark):
        """Return a new chunk, calling mark(tags) on portions of the old
        chunk that match regexp.
        """

        spans = [m.span() for m in re.finditer(regexp, str(self))]
        new = []
        prev = 0

        # make start and end relative
        for i, (start, end) in enumerate(spans):
            spans[i] = (start - prev, end - start)
            prev = end

        chunk = self
        for start, end in spans:
            before, chunk = chunk.slice(start)
            new.extend(before)
            within, chunk = chunk.slice(end)
            new.extend([(mark(tags), s) for (tags, s) in within])
        new.extend(chunk)
        return Chunk(new)

    @staticmethod
    def tag_reverse(tags):
        return tuple(set(tags) ^ {'reverse'})

    def slice(self, cut):
        """Return two new chunks split character-wise at cut."""

        left = []
        right = []
        off = 0
        i = 0
        for i, (tags, s) in enumerate(self.contents):
            l = len(s)
            if off + len(s) >= cut:
                if off != cut:
                    left.append((tags, s[:cut - off]))
                if l == 0 or cut - off < l:
                    right = [(tags, s[cut - off:])]
                break
            else:
                left.append((tags, s))
            off += l
        right.extend(self.contents[i + 1:])

        return Chunk(left), Chunk(right)