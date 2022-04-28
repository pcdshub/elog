#!/usr/bin/env python
"""
This is the replacement for the older Logbook clients that were shipped as
part of the grabber. Specifically, this replaces LogBookPost_self.py,
which is what hutch python was using mostly. The argparse seeks to mimic
the command line parameters for LogBookPost_self.py. This is implemented
using the PCDS elog client.
"""
import argparse
import logging
import subprocess

import elog

logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='A command-line utility \
        to post messages to the electronic logbook of a specified experiment.')
    parser.add_argument('-i', '--instrument', required=True,
                        help='The name of the instrument.')
    parser.add_argument('-e', '--experiment', required=True,
                        help='The name of an experiment on this instrument.')
    # Optional arguments start here
    parser.add_argument('-s', '--station', help='An optional station number. \
        If unspecified, we default to station 0', default=0, type=int)
    parser.add_argument('-w', '--webserviceurl',
                        default='https://pswww.slac.stanford.edu',
                        help='The logbook webservice endpoint.')
    parser.add_argument('-u', '--user',
                        help='User id for authentication. \
                        If using an operator account, please specify the \
                        operator account user id. If authenticating \
                        using Kerberos, please skip this.')
    parser.add_argument('-p', '--password',
                        help='Password for authentication. If authenticating \
                        using Kerberos, please skip this.')
    parser.add_argument('-r', '--run', help='An optional run number \
        that the log message will be associated with.')
    parser.add_argument('-m', '--message',
                        help='The text of the log message.')
    parser.add_argument('-t', '--tags',
                        help='Tags for the elog entry. Specify any number \
                        of tags as a list following this argument.', nargs='*')
    parser.add_argument('-a', '--attachments', help='Attach this file \
        as a attachment. Any number of attachments are supported. \
        Please specify them as a list of arguments after this parameter',
                        nargs='*')
    parser.add_argument('-c', '--commandforchild', help='Execute the command \
        and post the stdout as the body of a HTML message. The -m/--message \
        is used as the title for the message. By default, a <pre> tag is \
        automatically added  to the HTML message body for better formatting \
        To skip this automatic addition of a pre tag, use the \
        --skippre argument. Note: using this option may result in delays \
        resulting from the execution of the command to generate \
        the HTML body.')
    parser.add_argument('-k', '--skippre', default=False, action="store_true",
                        help='If posting a HTML message, skip the automatic \
                        addition of the <pre> tag.')
    args = parser.parse_args()

    params = {"run": args.run,
              "tags": args.tags,
              "attachments": args.attachments}
    if args.commandforchild:
        params["title"] = args.message
        html_body = subprocess.run(args.commandforchild.split(),
                                   capture_output=True).stdout.decode("utf-8")
        params["msg"] = html_body if args.skippre \
            else "<pre>" + html_body + "<pre>"
    else:
        params["msg"] = args.message

    if args.experiment:
        elog = elog.ELog(logbooks={"experiment": args.experiment},
                         user=args.user,
                         pw=args.password,
                         base_url=args.webserviceurl)
        elog.post(**params)
    else:
        elog = elog.HutchELog(args.instrument,
                              station=args.station,
                              user=args.user,
                              pw=args.password,
                              base_url=args.webserviceurl)
        params.update({"experiment": True, "facility": False})
        elog.post(**params)
