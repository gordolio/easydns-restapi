from optparse import OptionParser
from sys import argv
import json
import re
import atexit

from time import time

from easydns_restapi.client import Client

__version__ = '1.2.1'
__author__ = 'Puru Tuladhar <ptuladhar3@gmail.com>'


def info(self, msg):
    print("[INFO] [%s] %s" % (self.now(), msg))


def _atexit(self, s):
    d = time() - s
    if d > 60:
        d = d / 60
    info("script completed in %.2f seconds" % d)


def main():
    global EASYDNS_CONF

    message = "A command-line tool for managing (create/update) EasyDNS DNS records using easyDNS rest API."
    parser = OptionParser(usage=message, version="%%prog v%s written by %s" % (__version__, __author__))

    parser.add_option('-f', '--file', dest="conf",
                      help='configuration file containing easyDNS API details',
                      default=False)

    parser.add_option('-c', '--create', dest="create",
                      action="store_true",
                      help='create new record',
                      default=False)

    parser.add_option('-u', '--update', dest="update",
                      action="store_true",
                      help='update existing record to new IP address',
                      default=False)

    parser.add_option('-H', '--hostname', dest="hostname",
                      help="specify short hostname without domain name part. e.g: www for www.example.com",
                      metavar="HOSTNAME")

    parser.add_option('-a', '--address', dest="address",
                      help="specify IP address for the hostname",
                      metavar="IPADDR")

    (option, args) = parser.parse_args(argv)

    if not option.conf:
        parser.error("configuration file missing")

    try:
        EASYDNS_CONF = json.load(open(option.conf, 'r'))
    except Exception as loadex:
        parser.error(loadex)

    client = Client(EASYDNS_CONF)

    if option.create and option.update:
        parser.error("options --create and --update cannot be specified together")

    action = None

    if option.create:
        action = "create"
    elif option.update:
        action = "update"
    else:
        parser.error("option --create or --update must be specified")

    if not option.hostname or not option.address:
        parser.error("both option --hostname and --address must be specified")

    hostname = option.hostname.lower()
    address = option.address

    # validate hostname and address
    if '.' in hostname or not re.match("^[a-z][a-z0-9]*$", hostname):
        parser.error("invalid hostname specified")

    _invalid_address = "invalid ip address specified"
    if len(address.split('.')) is not 4:
        parser.error(_invalid_address)
    else:
        octets = address.split('.')
        try:
            octets = [int(octet) for octet in octets]
        except ValueError:
            parser.error(_invalid_address)
        for octet in octets:
            if octet < 0 or octet > 255:
                parser.error(_invalid_address)

    print("Press Ctrl-C to quit")
    client.info("script started (delay set to %s seconds)" % (EASYDNS_CONF.get('delay')))
    atexit.register(_atexit, time())

    # verify API token and key are valid
    # easydns_verify_api_token()

    if action == "create":
        client.easydns_create_record(hostname, address)
    elif action == "update":
        client.easydns_update_record(hostname, address)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
