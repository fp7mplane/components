/* 

Author:		Salvatore Balzano
Date:		2013.10.10
Description:	Capture network traffic in HAR file
Usage:		bin/phantomjs netsniff_SB.js 'url_to_browse'
	
Changelog v1.3 		1) Only dumping harfiles (no more loadtime and host)
			2) Timestamp changed in standard unix timestamp (number of seconds elapsed since 1 January 1970 )
			3) 2 seconds sleeping between each browsing sessions 

Changelog v1.4 		1) Random value for Request_id in HTTP header 

Changelog v1.5		1) Har file formatted in one single raw 
				"JSON.stringify(har, undefined)"	

Changelog v1.6		1) Har file in  /tmp/phantomjs.har
	   
*/
if (!Date.prototype.toISOString) {
    Date.prototype.toISOString = function () {
        function pad(n) { return n < 10 ? '0' + n : n; }
        function ms(n) { return n < 10 ? '00'+ n : n < 100 ? '0' + n : n }
        return this.getFullYear() + '-' +
            pad(this.getMonth() + 1) + '-' +
            pad(this.getDate()) + 'T' +
            pad(this.getHours()) + ':' +
            pad(this.getMinutes()) + ':' +
            pad(this.getSeconds()) + '.' +
            ms(this.getMilliseconds()) + 'Z';
    }
}


Date.prototype.toISOLocalDateTimeString = function() {
    var padDigits = function padDigits(number, digits) {
        return Array(Math.max(digits - String(number).length + 1, 0)).join(0) + number;
    }
    var offsetMinutes = this.getTimezoneOffset();
    var offsetHours = offsetMinutes / 60;
    var offset= "Z";    
    if (offsetHours < 0)     
      offset = "-" + padDigits(offsetHours.toString().replace("-","") + "00",4);
    else if (offsetHours > 0) 
      offset = "+" + padDigits(offsetHours  + "00", 4);
    function ms(n) { return n < 10 ? '00'+ n : n < 100 ? '0' + n : n }
    return this.getFullYear() 
            + "-" + padDigits((this.getUTCMonth()+1),2) 
            + "-" + padDigits(this.getUTCDate(),2) 
            + "T" 
            + padDigits(this.getUTCHours()-(offsetHours),2)
            + ":" + padDigits(this.getUTCMinutes(),2)
            + ":" + padDigits(this.getUTCSeconds(),2)
            + "." + ms(this.getUTCMilliseconds(),2)
            + offset;

}


if (!Date.prototype.toNormalString) {
        Date.prototype.toNormalString = function() {
        function pad(n) { return n < 10 ? '0' + n : n; }
        function ms(n) { return n < 10 ? '00'+ n : n < 100 ? '0' + n : n }
        return this.getFullYear() +
            pad(this.getMonth() + 1) +
            pad(this.getDate()) +
            pad(this.getHours()) +
            pad(this.getMinutes()) +
            pad(this.getSeconds()) +
            ms(this.getMilliseconds());
          }
        }       


function createHAR(address, title, startTime, elaspedTime, resources)
{
    var entries = [];

    resources.forEach(function (resource) {
        var request = resource.request,
            startReply = resource.startReply,
            endReply = resource.endReply;

        if (!request || !startReply || !endReply) {
            return;
        }

        // Exclude Data URI from HAR file because
        // they aren't included in specification
        if (request.url.match(/(^data:image\/.*)/i)) {
            return;
	}

        entries.push({
            startedDateTime: request.time.toISOLocalDateTimeString(),
            TimeToFirstByte: startReply.time.toISOLocalDateTimeString(),
            endtimeTS: endReply.time.toISOLocalDateTimeString(),
	    time: endReply.time - request.time,
            request: {
                method: request.method,
                url: request.url,
                httpVersion: "HTTP/1.1",
                cookies: [],
                headers: request.headers,
		//headers: [],                
		queryString: [],
                headersSize: -1,
                bodySize: -1
            },
            response: {
                status: endReply.status,
                statusText: endReply.statusText,
                httpVersion: "HTTP/1.1",
                cookies: [],
                headers: endReply.headers,
                redirectURL: "",
                headersSize: -1,
                bodySize: startReply.bodySize,
                content: {
                    size: startReply.bodySize,
                    mimeType: endReply.contentType
                }
            },
            cache: {},
            timings: {
                blocked: 0,
                dns: -1,
                connect: -1,
                send: 0,
                wait: startReply.time - request.time,
		receive: endReply.time - startReply.time,
                ssl: -1
            },
            pageref: address
        });
    });

    return {
        log: {
            version: '1.2',
            creator: {
                name: "PhantomJS",
                version: phantom.version.major + '.' + phantom.version.minor +
                    '.' + phantom.version.patch
            },
            pages: [{
                startedDateTime: startTime.toISOLocalDateTimeString(),
                id: address,
                title: title,
                pageTimings: {
		    onContentLoad : 0,
                    onLoad: elaspedTime
                }
            }],
            entries: entries
        }
    };
}

var page = require('webpage').create(),
    system = require('system');

if (system.args.length === 1) {
    console.log('Usage: netsniff.js <some URL>');
    phantom.exit(1);
} else {

    page.address = system.args[1];
    page.resources = [];
        
    //page.settings.userAgent = "Firefox 12 on WandBoard - Eurecom";   

    page.onLoadStarted = function () {
        page.startTime = new Date();
    };
       
    page.customHeaders = {"httpid" : "1"};
          
    page.onResourceRequested = function (req) {
        
        page.resources[req.id] = {            
            request: req,
            startReply: null,
            endReply: null
        };
	var random = Math.floor(Math.random()*2147483647);
	page.customHeaders = {"httpid" : random};                              
    };

    page.onResourceReceived = function (res) {
        if (res.stage === 'start') {
            page.resources[res.id].startReply = res;
        }
        if (res.stage === 'end') {
            page.resources[res.id].endReply = res;
        }
    };
    
    
    console.log('Start to fetch: ' + page.address);
    var called = 0;
    var t_start = new Date().getTime();
                
    page.open(page.address, function (status) {
	
        if (status !== 'success') {
            console.log('FAIL to load: ' + page.address);
            
        } else {
            if (called) {
		console.log(page.address + ' recalled');
                return;
            }
    
            called = 1;
            var t_end = new Date().getTime();
                                                                 
            page.title = page.evaluate(function () {
                return document.title;
            });
           
            console.log('[' + page.address + '] Loading time ' + (t_end - t_start) + ' msec');
            var har = createHAR(page.address, page.title, page.startTime, t_end - t_start, page.resources);
            var fs = require('fs');
            
	    try {		
		//Writing Har file		
		f = fs.open("/tmp/phantomjs.har", "w");
                f.writeLine(JSON.stringify(har, undefined, 4));
		//f.writeLine(JSON.stringify(har, undefined));
                f.close();		

            } catch (e) { console.log(e); }  
                       
            delete page;
            phantom.exit();
        }
          
    }); //end of page.open      
      
}
