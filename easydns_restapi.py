#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# The MIT License (MIT)
#
# Copyright (c) 2016-2020 Puru Tuladhar
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import requests
from sys import exit
from time import sleep, strftime, time
import json

__version__ = '1.2.1'
__author__  = 'Puru Tuladhar <ptuladhar3@gmail.com>'

EASYDNS_CONF = {}

def now():
	return strftime("%F %T %Z")

def delay(_seconds):
	''' Delay between subsequent API calls '''
	sleep(_seconds)

def info(msg):
	print ("[INFO] [%s] %s" % (now(), msg))

def error(msg, die=False):
	_red = "\033[31m"
	_reset = "\033[00m"
	print ("{red}[ERR!] [{date}] {msg}{reset}".format(red=_red, date=now(), msg=msg, reset=_reset))
	if die:
		exit(1)

def _atexit(s):
	d = time() - s
	if d > 60:
		d = d / 60
	info("script completed in %.2f seconds" % d)

def easydns_easy_request(method, url, data=None):
	''' Wrapper for API calls. Allowed methods are GET, POST and PUT'''
	_token	 = EASYDNS_CONF.get('token')
	_key	 = EASYDNS_CONF.get('key')
	_res	 = None
	_method  = method
	_url     = url
	_data    = None

	if _method is "POST" or method is "PUT":
		_data = data

	_success = "easydns API call successful (msg: %s, status: %s, code: %s)" 
	_failed  = "easydns API call failed: %s"
	_error   = "easydns API call returned error: %s (code: %s, url: %s)"

	try:
		delay(EASYDNS_CONF.get('delay'))
		if _method is "GET":
			_res = requests.get(_url, auth=(_token, _key))
		elif _method is "POST":
			_res = requests.post(_url, data=_data, auth=(_token, _key))
		elif _method is "PUT":
			_res = requests.put(_url, data=_data, auth=(_token, _key))
		else:
			error('method (%s) not implemented' % _method, True)
	except requests.RequestException as _res_failed:
		# API call failed.
		error(_failed % (_res_failed), True)
	else:
		try:
			_json = _res.json()
		except:
			error(_error % (_res.text, _res.status_code, _url), True)
		else:
			if _json.get('error', False):
			 	_msg = _json.get('error').get('message') or _res.reason
			 	_code = _json.get('error').get('code') or _res.status_code
			 	error(_error % (_msg, _code, _url), True)
			else:
				_msg = _json.get('msg') or _res.reason
				_code = _json.get('code') or _json.get('status') or _res.status_code
				_rstatus = _json.get("rstatus", "N/A")
				info(_success % (_msg, _code, _rstatus))
				return _json

def easydns_verify_api_token():
	''' Verify EasyDNS API token and keys
	    See: http://docs.sandbox.rest.easydns.net/2
	'''
	info('verifying API endpoint, token and keys...')
	_endpoint	= EASYDNS_CONF.get('endpoint')
	_format		= EASYDNS_CONF.get('format')
	_action		= "/domains/check/easydns.net"
	_url 		= "{endpoint}{action}?format={format}".format(endpoint=_endpoint, action=_action, format=_format)
	easydns_easy_request("GET", _url)

def easydns_create_record(hostname, address):
	''' Create new DNS record.
	    See: http://docs.sandbox.rest.easydns.net/9
	'''
	info('creating record %s.%s pointing to %s...' % (hostname, EASYDNS_CONF.get('domain'), address))
	_endpoint	= EASYDNS_CONF.get('endpoint')
	_format		= EASYDNS_CONF.get('format')
	_action		= "/zones/records/add/%s/A" % EASYDNS_CONF.get('domain')
	_url 		= "{endpoint}{action}?format={format}".format(endpoint=_endpoint, action=_action, format=_format)
	_data       = json.dumps({
		"domain": EASYDNS_CONF.get('domain'),
		"host": hostname,
		"ttl": EASYDNS_CONF.get("ttl"),
		"prio": 0,
		"type": "A",
		"rdata": address
	})
	easydns_easy_request("PUT", _url, _data)

def easydns_update_record(hostname, address):
	''' Update existing DNS record to new IP address
	    See: http://docs.sandbox.rest.easydns.net/10
	'''
	# find the unique ID (i.e, Zone ID) for the hostname
	info('checking %s.%s exists ...' % (hostname, EASYDNS_CONF.get('domain')))
	_endpoint	= EASYDNS_CONF.get('endpoint')
	_format		= EASYDNS_CONF.get('format')
	_action		= "/zones/records/all/%s" % EASYDNS_CONF.get('domain')
	_url 		= "{endpoint}{action}?format={format}".format(endpoint=_endpoint, action=_action, format=_format)
	_records	= easydns_easy_request("GET", _url)
	_zone_id 	= None
	_ttl		= None
	_last_mod   = None
	_old_address = None

	if _records.get("data"):
		_count = 0
		for _record in _records.get("data"):
			_count += 1
			_hostname = str(_record.get("host"))
			if hostname == _hostname:
				_zone_id = str(_record.get('id'))
				_old_address = str(_record.get('rdata'))
				_ttl = str(_record.get('ttl'))
				_last_mod = str(_record.get('last_mod'))
				break
		info("... total hostname searched: %s" % _count)

	if not _zone_id:
		error("hostname does not seem to exist!", True)

	info("hostname exists (zone ID: %s, ttl: %s, last modified: %s, address: %s)" % (_zone_id, _ttl, _last_mod, _old_address))
	info("updating record %s.%s pointing to %s ..." % (hostname, EASYDNS_CONF.get('domain'), address))
	_action		= "/zones/records/%s" % _zone_id
	_url 		= "{endpoint}{action}?format={format}".format(endpoint=_endpoint, action=_action, format=_format)
	_data		= json.dumps({
		"host": hostname,
		"ttl": EASYDNS_CONF.get('ttl'),
		"type": "A",
		"rdata": address,
	})
	easydns_easy_request("POST", _url, _data)
