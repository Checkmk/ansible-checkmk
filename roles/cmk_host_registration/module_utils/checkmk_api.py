#!/usr/bin/python
# -*- encoding: utf-8; py-indent-offset: 4 -*-

from collections import namedtuple
import ast
import requests

class WebAPI(object):
    def __init__(self, session):
        self.url = session.url
        self.username = session.username
        self.secret = session.secret
        self.verify = session.verify

        self.header = {
            'request_format': 'python',
            'output_format': 'python',
            '_username': self.username,
            '_secret': self.secret,
            }

    def query(self, action, request=None):
        payload = self.header.copy()
        payload['action'] = action
        if request:
            payload['request'] = repr(request)

        try:
            response = requests.get(self.url, params=payload, verify=self.verify, timeout=5)
            return ast.literal_eval(response.text)
        except:
            raise


    @property
    def result(self):
        return self.result


    @property
    def result_code(self):
        return self.result_code


class DataTuple(object):
    def __init__(self, url, username, secret, verify=True):
        name = namedtuple('name', ['url', 'username', 'secret', 'verify'])
        self.data = name(url, username, secret, verify)



class Hosts(object):
    def __init__(self, url, username, secret, verify=True, hostname=None):
        url = "%s/check_mk/webapi.py" % url.rstrip('/')
        session = DataTuple(url, username, secret, verify)
        self.session = WebAPI(session.data)
        self.hostname = hostname


    def pre_call(fn):
        def _decorator(self, *args, **kwargs):
            if len(args) > 0:
                hostname = args[0]
            else:
                hostname = kwargs.get('hostname', None)

            if not hostname:
                if not self.hostname:
                    return fn(None)
                hostname = self.hostname

            if kwargs.get('payload', None):
                payload = kwargs['payload']
            else: # we need to build the payload manually
                payload = {'hostname': hostname}
                payload['folder'] = kwargs.get('folder', '')
                if kwargs.get('attributes', None):
                    payload['attributes'] = kwargs['attributes']
                if kwargs.get('effective_attributes', None) in [1,0]:
                    payload['effective_attributes'] = kwargs['effective_attributes']

            return fn(self, payload=payload)
        return _decorator


    @pre_call
    def get(self, hostname=None, effective_attributes=None, payload=None):
        if not payload:
            return None
        get_payload = {'hostname': payload['hostname'],
                       'effective_attributes': payload['effective_attributes']
                       }
        return self.session.query('get_host', get_payload)


    @pre_call
    def add(self, hostname=None, folder=None, attributes=None, payload=None):
        if not payload:
            return None
        return self.session.query('add_host', payload)


    @pre_call
    def delete(self, hostname=None, payload=None):
        if not payload:
            return None
        del_payload = {'hostname': payload['hostname']}
        return self.session.query('delete_host', del_payload)


    @pre_call
    def edit(self, hostname=None, folder=None, attributes=None, payload=None):
        if not payload:
            return None
        return self.session.query('edit_host', payload)


class Services(object):
    def __init__(self, url, username, secret, verify=True, hostname=None):
        url = "%s/check_mk/webapi.py" % url.rstrip('/')
        session = DataTuple(url, username, secret, verify)
        self.session = WebAPI(session.data)
        self.hostname = hostname


    def pre_call(fn):
        def _decorator(self, *args, **kwargs):
            if len(args) > 0:
                hostname = args[0]
            else:
                hostname = kwargs.get('hostname', None)

            if not hostname:
                if not self.hostname:
                    return fn(None)
                hostname = self.hostname

            if kwargs.get('payload', None):
                payload = kwargs['payload']
            else:
                payload = {'hostname': hostname}
                if kwargs.get('mode', None):
                    payload['mode'] = kwargs['mode']

            return fn(self, payload=payload)
        return _decorator

    @pre_call
    def discover(self, hostname=None, mode=None, payload=None):
        if not payload:
            return None
        return self.session.query('discover_services', payload)


class Changes(object):
    def __init__(self, url, username, secret, verify=True):
        url = "%s/check_mk/webapi.py" % url.rstrip('/')
        session = DataTuple(url, username, secret, verify)
        self.session = WebAPI(session.data)

    def pre_call(fn):
        def _decorator(self, **kwargs):
            if kwargs.get('payload', None):
                payload = kwargs['payload']
            else:
                payload = {}
                if kwargs.get('sites', None):
                    payload['mode'] = 'specific'
                    payload['sites'] = list(kwargs['sites'])
                if kwargs.get('allow_foreign_changes', None):
                    payload['allow_foreign_changes'] = str(kwargs['allow_foreign_changes'])
                if kwargs.get('comment', None):
                    payload['comment'] = str(kwargs['comment'])
            return fn(self, payload=payload)
        return _decorator


    @pre_call
    def activate(self, sites=None, allow_foreign_changes=None, comment=None, payload=None):
        return self.session.query('activate_changes', payload)
