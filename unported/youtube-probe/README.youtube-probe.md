# YouTube-Probe initial implementation for the mplane-RI

This code implements a YouTube active probe within the mplane Reference Implementation framework.

The probe downloads a YouTube video (specified by the 11-character ```video_id```), emulates playback, 
and calculates the following metrics for the download:

| Metric | Description | 
| ------ | ----------- |
| ```rebuffer.events``` | number of video stalls | 
| ```delay.buffering.ms``` | totel buffering time | 
| ```octets.layer7``` | number of bytes downloaded | 
| ```delay.download.ms``` | total download time |
| ```delay.urlresolve.ms``` | time needed to resolve video URL | 
| ```delay.srvresponse.ms``` | delay of 1st reply packet after request | 
| ```bandwidth.min.bps``` | worst bitrate (of 1sec intervals) |
| ```bandwidth.max.bps``` | best bitrate (of 1sec intervals) |
| ```bandwidth.avg.bps``` | average bitrate (of 1sec intervals) |

The probe terminates playback emulation when the download is complete, i.e. usually it finishes sooner than the 
video duration.

Currently, the only supported is format **5** (*FLV*). 
Consult table *Comparison of YouTube media encoding options* in http://en.wikipedia.org/wiki/YouTube#Video_technology
for more details on the FLV format.

# Usage

```yp-test.py``` is a command line frontend for the probe module. Use
   PYTHONPATH=. python3 yp-test.py -h
for a list of options, the basic use case is:
    PYTHONPATH=. python3 yp-test.py 8tz0Y_eZ3Vo
if no ```video_id``` is provided, the default is *riyXuGoqJlY*

# Requirements

* (whatever is required by the mplane RI), currenly:
  * python3
  * pyyaml
* pyCURL
* _youtube-dl_ package needs to be installed ( https://github.com/rg3/youtube-dl )
