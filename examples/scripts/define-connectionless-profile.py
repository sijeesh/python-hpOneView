#!/usr/bin/env python3
###
# (C) Copyright 2015 Hewlett-Packard Development Company, L.P.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
###
import sys
if sys.version_info < (3, 4):
    raise Exception('Must use Python 3.4 or later')

import hpOneView as hpov
from pprint import pprint
import json


def acceptEULA(con):
    # See if we need to accept the EULA before we try to log in
    con.get_eula_status()
    try:
        if con.get_eula_status() is True:
            print('EULA display needed')
            con.set_eula('no')
    except Exception as e:
        print('EXCEPTION:')
        print(e)


def login(con, credential):
    # Login with givin credentials
    try:
        con.login(credential)
    except:
        print('Login failed')


def define_profile(srv, sts, profileName, serverHWName, serverIP,
                   baseline, forcePowerOff=False):

   # Find the first Firmware Baseline
    uri = ''
    if baseline:
        spps = sts.get_spps()
        for spp in spps:
            if spp['isoFileName'] == baseline:
                uri = spp['uri']
        if not uri:
            print('ERROR: Locating Firmeware Baseline SPP')
            print('Baseline: "%s" can not be located' % baseline)
            print('')
            sys.exit()

    # Get handle for named server and power off in necessary
    servers = srv.get_servers()
    ser = None
    for server in servers:
        if server['name'] == serverHWName or serverIP ==server['mpIpAddress']:
            ser = server
            if server['state'] != 'NoProfileApplied':
                print('Server ', serverHWName, '  may already have a profile')
                sys.exit(1)
            if server['powerState'] == 'On':
                if forcePowerOff:
                    srv.set_server_powerstate(server, 'Off', force=True)
                else:
                    print('Error: Server', serverHWName,
                          ' needs to be powered off')
                    sys.exit(1)
            break
    if not ser:
        print('Server ', serverHWName, ' not found')
        sys.exit(1)

    if not uri:
        profileDict = hpov.common.make_conectionless_profile_dict(profileName,
                                                    ser)
    else:
        fwBaseline = hpov.common.make_profile_firmware_baseline(uri)
        profileDict = hpov.common.make_conectionless_profile_dict(profileName,
                                                    ser, fwBaseline)

    profile = srv.create_server_profile(profileDict)
    pprint(profile)


def main():
    parser = argparse.ArgumentParser(add_help=True,
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     description='''
    Define a connectionless profile for a standalone server''')
    parser.add_argument('-a', dest='host', required=True,
                        help='''
    HP OneView Appliance hostname or IP address''')
    parser.add_argument('-u', dest='user', required=False,
                        default='Administrator',
                        help='''
    HP OneView Username''')
    parser.add_argument('-p', dest='passwd', required=False,
                        help='''
    HP OneView Password''')
    parser.add_argument('-c', dest='cert', required=False,
                        help='''
    Trusted SSL Certificate Bundle in PEM (Base64 Encoded DER) Format''')
    parser.add_argument('-r', dest='proxy', required=False,
                        help='''
    Proxy (host:port format''')
    parser.add_argument('-n', dest='name',
                        required=True,
                        help='''
    Name of the profile''')
    parser.add_argument('-f', '--forcePowerOff', dest='forcePowerOff',
                        required=False,
                        action='store_true',
                        help='''
    When set, forces power off of target server.
    Avoids error exit if server is up''')
    parser.add_argument('-s', dest='baseline', required=False,
                        help='''
    SPP Baseline file name. e.g. SPP2013090_2013_0830_30.iso''')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-sn', dest='serverHW',
                        help='''
    Name of the standalone server hardware which this profile is for''')
    group.add_argument('-si', dest='serverIP',
                        help='''
    IP address of the standalone server iLO''')

    args = parser.parse_args()
    credential = {'userName': args.user, 'password': args.passwd}

    con = hpov.connection(args.host)
    srv = hpov.servers(con)
    sts = hpov.settings(con)

    if args.proxy:
        con.set_proxy(args.proxy.split(':')[0], args.proxy.split(':')[1])
    if args.cert:
        con.set_trusted_ssl_bundle(args.cert)

    login(con, credential)
    acceptEULA(con)

    define_profile(srv, sts, args.name, args.serverHW, args.serverIP,
                   args.baseline, args.forcePowerOff)

if __name__ == '__main__':
    import sys
    import argparse
    sys.exit(main())

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
