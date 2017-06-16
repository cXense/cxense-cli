#!/usr/bin/env python
"""\
Execute API requests.

Usage: cx.py <api path> <request object>

    Authentication is done by generating the appropriate header after reading the
    line 'authentication <username> <api key>' from ~/.cxrc.

    JSON will be seralized according to the default encoding, or ascii safe if
    in doubt.

    Stdin will be used if request object is "-". If no request object, the
    empty object "{}" is assumed.

Wiki references and documentation:
    API authentication: https://wiki.cxense.com/display/cust/API+authentication
    Requests and responses: https://wiki.cxense.com/display/cust/Requests+and+responses

Examples (for bash, please check the wiki pages for tips how to run this on Windows)

    Version:
        $ cx.py --version
        VERSION cx.py : <version>

    Absolute path:
        $ cx.py https://api.cxense.com/public/date
        {
              "date": "2013-04-22T15:06:20.252Z"
        }

    Relative path, defaults to https://api.cxense.com unless apiserver is set in ~/.cxrc
        $ cx.py /public/date
        {
              "date": "2013-04-22T15:06:20.252Z"
        }

    POST request with non-empty request object:
        $ cx.py /site '{"siteId":"9222300742735526873"}'
        {
          "sites": [
            {
              "id": "9222300742735526873"
              "name": "Example site",
              "url": "http://www.example.com",
              "country": "US",
              "timeZone": "America/Los_Angeles",
            }
          ]
        }

    GET request with json parameter:
        $ cx.py /profile/content/fetch?json=%7B%22url%22%3A%22http%3A%2F%2Fwww.example.com%22%7D
        {
          "url": "http://www.example.com",
          "id": "0caaf24ab1a0c33440c06afe99df986365b0781f"
        }

"""

import sys
def isPython2():
    return sys.version_info.major == 2

if isPython2():
    import httplib
    import urlparse
else:
    import http.client as httplib
    import urllib.parse as urlparse

import os
import hmac
import json
import locale
import hashlib
import datetime
import traceback
import collections

#
# please update the version
#
VERSION_TIMESTAMP = '2017-06-09'

# Default configuration.
username = None
secret = None
apiserver = 'https://api.cxense.com'

# Locate and autoload configuration from ~/.cxrc
rc = os.path.join(os.path.expanduser('~'), '.cxrc')
if os.path.exists(rc):
    for line in open(rc):
        fields = line.split()
        if fields[0] == 'authentication' and len(fields) == 3:
            username = fields[1]
            secret = fields[2]
        elif fields[0] == 'apiserver' and len(fields) == 2:
            apiserver = fields[1]

def getDate(connection):
    # If the computer's time can be trusted, the below condition can be changed to False
    if True:
        try:
            connection.request("GET", "/public/date")
            return json.load(connection.getresponse())['date']
        except:
            pass

    return datetime.datetime.utcnow().isoformat() + "Z"

def execute(url, content, username=username, secret=secret):
    connection = (httplib.HTTPConnection if url.scheme == 'http' else httplib.HTTPSConnection)(url.netloc)

    try:
        date = getDate(connection)
        signature = hmac.new(secret.encode('utf-8'), date.encode('utf-8'), digestmod=hashlib.sha256).hexdigest()
        headers = {"X-cXense-Authentication": "username=%s date=%s hmac-sha256-hex=%s" % (username, date, signature)}
        headers["Content-Type"] = "application/json; charset=utf-8"
        connection.request("GET" if content is None else "POST", url.path + ("?" + url.query if url.query else ""), content, headers)
        response = connection.getresponse()
        return response.status, response.getheader('Content-Type', ''), response.read()

    finally:
        connection.close()

if __name__ == "__main__":
    # output the version number of this script
    if ('-v' in sys.argv) or ('--version' in sys.argv):
        print('VERSION cx.py : %r\n' % VERSION_TIMESTAMP)
        sys.exit()

    if len(sys.argv) < 2 or '--help' in sys.argv:
        print('VERSION cx.py: %r\n' % VERSION_TIMESTAMP)
        print(__doc__)
        sys.exit(1)

    elif len(sys.argv) > 3:
        print("Too many arguments. Remember to quote the JSON.")
        sys.exit(1)

    if username is None or secret is None:
        print("Please add the line 'authentication <username> <api key>' to %s" % rc)
        sys.exit(3)

    if '@' not in username:
        print("Username is not an email address: %s" % username)
        sys.exit(4)

    if not secret.startswith('api&'):
        print("Invalid API key: %s" % secret)
        sys.exit(5)

    # Load data from argument or stdin, hopefully with correct encoding.
    argument = sys.argv[2] if len(sys.argv) > 2 else None

    if argument is None:
        content = None

    elif argument == '-':
        content = sys.stdin.read()

    else:
        if isPython2():
            content = unicode(argument, sys.stdin.encoding or locale.getpreferredencoding()).encode('UTF-8')
        else:
            content = argument.encode('UTF-8')

    if len(sys.argv) == 2:
        try:
            # GET request: early integrity check of optional json query parameter
            # if no json parameter exists (like for /public/date), make the test pass with "{}" as dummy instead
            json.loads(urlparse.parse_qs(urlparse.urlparse(sys.argv[-1]).query).get('json',["{}"])[-1])

        except ValueError as e:
            print("Invalid JSON in \"json\" parameter: %s" % e)
            sys.exit(3)

    # Make sure piping works, which can have a undefined encoding.
    ensure_ascii = sys.stdout.encoding != 'UTF-8'

    # Default to apiserver, unless a full URL was given.
    path = sys.argv[1]
    if path.startswith('http'):
        url = urlparse.urlparse(path)
    else:
        url = urlparse.urlparse(urlparse.urljoin(apiserver, path))

    # Execute the API request and exit 0 only if it was successful.
    try:
        status, contentType, response = execute(url, content, username, secret)
    except:
        print("HTTP request to %s failed" % path)
        traceback.print_exc() 
        sys.exit(6)

    if contentType.startswith('application/json'):
        print(json.dumps(json.loads(response.decode('utf-8'), object_pairs_hook=collections.OrderedDict), indent=2, ensure_ascii=ensure_ascii))
    else:
        if isPython2():
            if sys.platform == "win32":
                # On Windows, stdout is text mode by default. Set binary mode to prevent mangling. Not needed in
                # Python 3, where sys.stdout.buffer.write ensures binary mode.
                import os, msvcrt
                msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
            sys.stdout.write(response)
        else:
            sys.stdout.buffer.write(response)
    if status != 200:
        sys.exit(1)
