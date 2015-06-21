#!/usr/bin/python3
import os
import logging
import socket
import json

logger = logging.getLogger(__name__)

def clean_tmp_files(backupdir, outfilelist, sessionurl, error=False):
    if error:
        for fname in outfilelist:
            try:
                os.remove(fname)
                logger.info("Removed {}".format(fname))
            except FileNotFoundError:
                logger.error("File not found: {}".format(fname))
    else:
        for fname in outfilelist:
            fn = os.path.join(backupdir, fname.split('/')[-1] + "_{}".format(sessionurl))
            os.rename(fname, fn)
            logger.info("moved {0} to {1}".format(fname, fn))


def valid_ip(address):
    """

    :param address: ip address to check
    :return: True if valid IP
    """
    try:
        socket.inet_aton(address)
        return True
    except socket.error:
        return False


def add_prefix(c, prefix):
    """

    :param c: dict
    :param prefix: string
    :return: updated dictionary with prefix-key
    """
    result = {}
    if isinstance(c, dict):
        for key, value in c.items():
            result['%s_%s' % (prefix, key)] = value
    elif isinstance(c, list):
        for tup in c:
            result['%s_%s' % (prefix, tup[0])] = tup[1]
    return result


def flatten(d, parent_key='', sep='_'):
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def flatten_active(dic):
    result = {'ping': [], 'trace': []}
    for k, v in dic.items():
        if valid_ip(k) and isinstance(v, dict): # active dic
            new_dic = {}
            for typ, measure in v.items():
                if typ == "ping":
                    new_dic = add_prefix(json.loads(measure), typ)
                    result['ping'].append(sorted(list(new_dic.items())))
                else: # 'trace'
                   if isinstance(measure, str):
                       for el in json.loads(measure):
                           tmp = flatten(el)
                           tmp['endpoints'] = ";".join(tmp['endpoints'])
                           new_dic = add_prefix(tmp, typ)
                           result['trace'].append(sorted(list(new_dic.items())))
    return result


def flatten_list(list_):
    result = []
    for el in list_:
        tmp = add_prefix(el, 'secondary')
        ordered = sorted(list(tmp.items()))
        result.append(ordered)
    return result


def flatten_probeid(dic):
    result = {}
    for k, v in dic.items():
        if isinstance(v, dict):
            for k1, v1 in v.items():
                new_key = k + "_" + k1
                result[new_key] = v1
        else:
            result[k] = v
    return result


def prepare_for_csv(dic):
    result = {}
    for key, value in dic.items():
        if isinstance(value, dict):
            if key == 'active_measurements':
                flattened = flatten_active(value)
                result.update(flattened)
            elif key == 'local_diagnosis':
                result.update(add_prefix(value, 'local_diag'))
            elif key == 'probeid':
                flattened = flatten_probeid(value)
                result.update(flattened)
        elif isinstance(value, list):  # services
            flattened = flatten_list(value)
            result['services'] = flattened
        else:
            result[key] = value
    return result
