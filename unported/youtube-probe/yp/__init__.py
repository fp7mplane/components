#
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
#
# YouTubeClient for evaluating downloads
#

import logging
import os
import subprocess
from threading import Timer
import time

import pycurl

from flvlib.tags import FLV, VideoTag, AudioTag
from flvlib.primitives import get_ui24,get_ui8
from yp.utils import SeekableByteQueue

log = logging.getLogger('youtube-probe')

class PlayerState:
    UNINITIALIZED = 0
    BUFFERING = 1
    PLAYING = 2
    REBUFFERING = 3
    FINISHED = 4

    def __str__(state):
        if state == UNINITIALIZED:
            return 'UNINITIALIZED'
        elif state == BUFFERING:
            return 'BUFFERING'
        elif state == 'PLAYING':
            return 'PLAYING'
        elif state == 'REBUFFERING':
            return 'REBUFFERING'
        elif state == 'FINISHED':
            return 'FINISHED'
        else:
            return 'INVALID'

class Player(SeekableByteQueue):
    """ Abstract class for a Player emulator  that is fed a byte stream by the downloader """

    def __init__(self):
        SeekableByteQueue.__init__(self)
        self._state = PlayerState.UNINITIALIZED
        # we're buffering at this offset - if not 0, rebuffering has happened
        self._mediaOffset = 0
        # wallclock time when we started playout
        self._playStartTime_Wallclock = None
        # when we started playout relative to the media's start 
        self._lastStatusPrint = 0
        self._underrunTimer = None

    def changeState(self, newstate):
        """ use to change player state """
        now = time.time()
        if newstate == PlayerState.BUFFERING:
            self._bufferingStarted = now
            log.info('Player starts BUFFERING')
        elif newstate == PlayerState.PLAYING:
            action = 'starts'
            if self._state == PlayerState.REBUFFERING:
                action = 'resumes'
            YouTubeClient.singleton._metrics['delay.buffering.ms'] += now - self._bufferingStarted
            self._playStartTime_Wallclock = now
            log.info('Player %s PLAYING, buffered: %04.03f secs' % ( action, self.getBufferedSeconds(self._mediaOffset)))
        elif newstate == PlayerState.REBUFFERING:
            self._bufferingStarted = now
            log.info('Player starts REBUFFERING')
            self._playStartTime_Wallclock = None
        elif newstate == PlayerState.FINISHED:
            if self._state == PlayerState.BUFFERING or self._state == PlayerState.REBUFFERING:
                 YouTubeClient.singleton._metrics['delay.buffering.ms'] += now - self._bufferingStarted
            log.info('Player FINISHED')
        self._state = newstate

    def feed(self, data):
        """ new data is pushed in by the downloader """
        if (self._state == PlayerState.BUFFERING or self._state == PlayerState.REBUFFERING) and self.getBufferedSeconds(self._mediaOffset) > 3:
            log.info("3 seconds of media buffered, starting playout") 
            self.changeState(PlayerState.PLAYING)
        if self._state == PlayerState.PLAYING:
            if self._underrunTimer != None:
                self._underrunTimer.cancel()
            t = time.time()
            # underrun happens when we run out of the buffered media. to calculate:
            # (in the buffer beyond the playout offset) - (number of seconds since we're playing it out)
            buffered = self.getBufferedSeconds(self._mediaOffset) - (t - self._playStartTime_Wallclock)
            self._underrunTimer = Timer(buffered, self.underrunEvent, [ self.getBufferedSeconds()] )
            self._underrunTimer.start()
            if (t - self._lastStatusPrint) > 1:
                self._lastStatusPrint = t
                log.debug('Media is Playing from offset %04.03f, buffered: %04.03f' % (self._mediaOffset, buffered))

    def getBufferedSeconds(self, offset = 0):
        """ how many seconds of video in the buffer (counting from offset) """
        raise NotImplementedError()

    def getLastMediaTimeStamp(self):
        """ get the presentation TS of the last complete frame """
        raise NotImplementedError()

    def underrunEvent(self, stallPTS):
        """ ran out of media buffer """
        YouTubeClient.singleton._metrics['rebuffer.counter'] = YouTubeClient.singleton._metrics['rebuffer.counter'] + 1
        log.info('Player stalled at %04.03f secs of media' % stallPTS)
        self._mediaOffset = stallPTS
        self.changeState(PlayerState.REBUFFERING)

    def __str__(self):
        return 'MediaPlayer(state %s, lastTimeStamp: %04.3f' % (PlayerState.str(self._state), self.getLastMediaTimeStamp())


class FLVPlayer(Player):
    """ Reads a FLV stream and emulates playout by advancing the stream as time passes """
    FILE_HEADER_SIZE = 9
    TAG_HEADER_SIZE = 15

    def __init__(self):
        Player.__init__(self)
        self._lastAudioTS = 0
        self._lastVideoTS = 0
        self.flv = FLV(self)

    def feed(self, data):
        """ input downloaded media data here piece by piece """
        self.put(data)

        # nothing parsed yet
        if self.tell() == 0:
            self.changeState(PlayerState.BUFFERING)
            if self.availBytes() >= self.FILE_HEADER_SIZE:
                self.flv.parse_header()
        else:
            tag = 0
            while tag != None:
                avail = self.availBytes()
                tag = None
                if avail >= self.TAG_HEADER_SIZE:
                    # peek for tag size
                    tag_type = get_ui8(self)
                    tag_size = get_ui24(self)
                    # log.debug("peek: %02X %u, available: %u" % (tag_type,tag_size,avail))
                    self.seek(-4, os.SEEK_CUR)
                    # size + next header size
                    if avail >= tag_size + self.TAG_HEADER_SIZE:
                        tag = self.flv.get_next_tag()
                        if type(tag) == VideoTag:
                            self._lastVideoTS = tag.timestamp
                            # log.debug("lastVideo: %u", self._lastVideoTS)
                        elif type(tag) == AudioTag:
                            self._lastAudioTS = tag.timestamp
                            # log.debug("lastAudio: %u", self._lastAudioTS)
            super(FLVPlayer, self).feed(data)

    def getLastMediaTimeStamp(self):
        """ get the presentation TS of the last complete frame """
        raise NotImplementedException()
        return min(self._lastVideoTS, self._lastAudioTS) / 1000.0

    def getBufferedSeconds(self, offset = 0):
        """ until when the buffer contains media """ 
        return  (min(self._lastVideoTS, self._lastAudioTS) / 1000.0) - offset
        
    def __str__(self):
        return ' FLVPlayer(unparsed bytes: %d, last A/V TS: %u/%u)' % \
            (self.availBytes(), self._lastAudioTS, self._lastVideoTS)


class MediaNotFound(Exception):
    pass

def writeFunction(data):
    if YouTubeClient.singleton != None:
        YouTubeClient.singleton.receive(data)

def bwstats():
    """ BW Statistics, called on every sec """
    ytclient = YouTubeClient.singleton
    ytclient._bwstats = None
    now = time.time()

    downloaded = ytclient._metrics['octets.layer7']
    bps = (downloaded - bwstats._lastBytes) * 8.0  
    bwstats._lastBytes = downloaded

    _min = ytclient._metrics['bandwidth.min.bps']
    _max = ytclient._metrics['bandwidth.max.bps']
    # log.debug("tick: %s bps: %s" % (str(now), str(bps)))
    if bps > _max:
        ytclient._metrics['bandwidth.max.bps'] = bps
    if bps < _min or _min <= 0:
        ytclient._metrics['bandwidth.min.bps'] = bps

    calc_delay = time.time() - now
    ytclient._bwstats = Timer(1.0 - calc_delay, bwstats)
    ytclient._bwstats.start()

class YouTubeClient(object):
    """Downloads a YouTube FLV video and evaluates download quality""" 

    singleton = None

    def __init__(self, params):
        YouTubeClient.singleton = self
        # this is just for logging purposes
        self.epoch = time.time()
     
        self._video_id = 'riyXuGoqJlY'  # default
        if 'video_id' in params:
            self._video_id = params['video_id']
        
        self.player = FLVPlayer()
        self._curl = pycurl.Curl()
        self._curl.setopt(pycurl.WRITEFUNCTION, writeFunction)
        self._curl.setopt(pycurl.CONNECTTIMEOUT, 5)
        if params['bwlimit'] != None:
            self._curl.setopt(pycurl.MAX_RECV_SPEED_LARGE, params['bwlimit'])
            log.info('Limiting pycurl bandwidth to %d' %  params['bwlimit'])
        # self._curl.setopt(curl.TIMEOUT, 5)

        self._bwstats = None # 
        
        self._metrics = { 
            'octets.layer7': 0,
            'delay.download.ms': 0,
            'bandwidth.min.bps': 0, 'bandwidth.max.bps': 0, 'bandwidth.avg.bps': 0,
            'delay.urlresolve.ms': 0,
            'delay.srvresponse.ms': 0,
            'delay.buffering.ms': 0,
            'rebuffer.counter': 0
        }

    def getURL(self):
        """ Figure out the URL for the video using youtube_dl """
        url = None
        try:
            url = subprocess.check_output(
                ["youtube-dl",'--default-search', 'auto', '-g','-f', '5', self._video_id], 
                stderr=None ).decode('UTF-8') 
        except subprocess.CalledProcessError as e:
            raise MediaNotFound(self._video_id)
        return url

    def receive(self, data):
        """ receive data from YouTube """
        if self._metrics['delay.srvresponse.ms'] == 0:
            self._metrics['delay.srvresponse.ms'] = (time.time() - self._http_start_time) * 1000.0

        self._metrics['octets.layer7'] += len(data)
        self.player.feed(data)

    def run(self):
        """ Execute """
        self._start_time = time.time()
        log.info('Query for media URL')
        try:
            self._url = self.getURL()
            # log.debug('URL: %s' % self._url)
            self._curl.setopt(pycurl.URL, self._url)
            self._metrics['delay.urlresolve.ms'] = (time.time() - self._start_time) * 1000.0
            self._http_start_time = time.time()
            log.info('URL extacted, starting download')

            # start BW stats now
            bwstats._lastBytes = 0
            self._bwstats = Timer(1.0, bwstats)
            self._bwstats.start()
            self._curl.perform()
            self._state = PlayerState.FINISHED
            self._metrics['delay.download.ms'] = (time.time() - self._http_start_time) * 1000.0
            self._metrics['bandwidth.avg.bps'] = 8.0 * self._metrics['octets.layer7'] \
                / (self._metrics['delay.download.ms'] / 1000.0)
            log.info("Download finished")
            self._curl.close()
        except Exception:
            self._metrics = {}
        finally:
            if self._bwstats:
                self._bwstats.cancel()
            if self.player._underrunTimer != None:
                self.player._underrunTimer.cancel()
        return (self._metrics == {}, self._metrics)

    def __str__(self):
        return ("YouTubeClient of video_id %s, metrics: %s " % (self._video_id, str(self._metrics)))
	
