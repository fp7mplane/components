#
#  vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
#

import os
import time
from logging import Formatter

class MyLogFormatter(Formatter):
    epoch = time.time()
    def format(self, record):
            return '[%s] %04.03f %s' % (record.levelname, time.time() - MyLogFormatter.epoch, record.getMessage())


class InternalError(Exception):
    """ signals a situationthat is not supposed to happen """
    pass

class SeekableByteQueue(object):
    """ Simple byte queue that behaves like a seekable file AS MUCH AS REQUIRED FOR FLV parsing """
    RETAIN_BYTES = 512

    def __init__(self):
        self._buffer = bytearray()
        self._offset = 0    # f.tell() gets self._offset + self._discarded
        self._discarded = 0

    def len(self):
        return len(self._buffer)
    
    def tell(self):
        return self._offset + self._discarded

    def availBytes(self):
        return len(self._buffer) - self._offset

    def get(self, size):
        """ remove 'size' bytes from the queue. Throws InternalError if not enough bytes to satisfy sizey """

        if self._offset + size > len(self._buffer):
            raise InternalError("Trying to read past the buffer, len: %u, offset: %d, discarded: %d,  size: %d" % \
                (len(self._buffer), self._offset, self._discarded, size))

        # get the data slice
        pos = self._offset + size
        ret = bytes(self._buffer[self._offset:pos])
        # advance the offset
        self._offset += size

        # we need to keep at most RETAIN_BYTES 
        if self._offset > self.RETAIN_BYTES:
            pos = self._offset - self.RETAIN_BYTES
            del self._buffer[0:pos]
            self._discarded += pos
            self._offset = self.RETAIN_BYTES
        return ret

    def peek(self, size):
        if self._offset + size > len(self._buffer):
            raise InternalError("Trying to peek past the buffer, len: %u, offset: %d, discarded: %d,  size: %d" % \
                (len(self._buffer), self._offset, self._discarded, size))
        return self._buffer[self._offset:self._offset+size]

    def read(self, size):
        return self.get(size)

    def put(self, data):
        self._buffer += data

    def seek(self, offset, whence = os.SEEK_SET):
        if whence == os.SEEK_END:
            raise InternalError("Seeking via SEEK_END")
        if whence == os.SEEK_SET:
            if offset != 0:
                raise InternalError("Seeking via os.SEEK_SET with a non-zero offset!")
            return
        if whence != os.SEEK_CUR:
            raise InternalError("Illegal seek, whence: %d" % whence)

        offset = self._offset + offset

        if offset > self.len() or offset < 0:
            raise InternalError("Seeking outside of the queue, len: %u offset: %u" % (self.len(), offset))

        self._offset = offset

    def __str__(self):
        return 'ByteQueue(len: %u, offset: %d, discarded: %d)' % (len(self._buffer), self._offset, self._discarded)


