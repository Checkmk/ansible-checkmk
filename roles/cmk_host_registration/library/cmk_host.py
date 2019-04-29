#!/usr/bin/python
# -*- encoding: utf-8; py-indent-offset: 4 -*-

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '0.1'}

DOCUMENTATION = '''
module: cmk_host

short_description: Access to WebAPI of Check_MK

version_added: "0.1"

description:
    - "With this module it is possible to add/edit/delete hosts or folders"
    - "It is further possible to do the service discovery on a host and activate these changes"
    - "Access to further capabilities of Check_MK may added later"

author: "Mathias Kettner GmbH"

options:
    site:
        description:
            - URL to the Check_MK instance as HTTP or HTTPS
        required: true
    user:
        description:
            - The user to authenticate against the site
        required: true
    password:
        description:
            - The password to authenticate against the site
        required: true
    name:
        description: Name of the host
        required: true
    alias:
        description: An Alias of the host
        required: false
    folder:
        description: Folder to put the host in
        required: false
        default: ''
    address_family:
        description: Set IP family to use
        required: false
        default: ipv4
        choices:
            - ipv4
            - ipv6
            - all
            - no
    addressv4:
        description: IPv4 address to assign to the host
        required: false
    addressv6:
        description: IPv6 address to assign to the host
        required: false
    snmp:
        description: If the host should be monitored by snmp
        required: false
        default: none
        choices:
            - snmpv1
            - snmpv2/v3
            - no
    agent:
        description: If the host should be monitored by agent or datasource program
        required: false
        default: agent
        choices:
            - agent
            - datasources
            - all
            - no
    parents:
        description: Parents of the host
        required: false
    state:
        description: If present, the host will be created if it does not exists yet. If absent, the host will remove, if present.
        required: false
        default: present
        choices:
            - present
            - absent
    validate_certs:
        description: Check SSL certificate
        required: false
        default: yes
        choices:
            - yes
            - no
'''

EXAMPLES = '''
- name: Add host to Check_MK site
  cmk_host:
    url: https://monitoring.example.org/mysite
    user: myuser
    password: mypassword
    name: myhost1

- name: Add host with specific folder and with explcit ip address
  cmk_host:
    url: https://monitoring.example.org/mysite
    user: myuser
    password: mypassword
    name: {{ inventory_hostname }}
    folder: automation/linux
    addressv4: 192.168.56.42
'''

RETURN = '''
request:
    - description: The paramters that was passed in
    type: dict
result:
    - description: The result from the Check_MK site
    type: dict
result_code:
    - description: The result code that was passed to the output
    type: int
'''

from ansible.module_utils.basic import AnsibleModule
import requests
import ast

class cmk_host:
    def __init__(self, url, payload, ansible):
        self._url = url
        self._payload = payload
        self._ansible = ansible
        self._session = requests.Session()
        if ansible.params['validate_certs'] == 'yes':
            self._verify = True
        else:
            self._verify = False
        self.result = ""
        self._result_code = 0


    def _query(self, action, request):
        self._payload['action'] = action
        self._payload['request'] = repr(request)
        try:
            response = eval(self._session.post(self._url, params=self._payload, verify=self._verify).text)
            self.result = response['result']
            self.result_code = response['result_code']
        except requests.exceptions.RequestException as err:
            self._ansible.fail_json(msg=str(err), payload=self._payload)


    def get(self):
        self._query('get_host', {'hostname': self._ansible.params['name'], 'effective_attributes':1})


    def add(self):
        request = dict(
                hostname = self._ansible.params['name'],
                folder = self._ansible.params.get('folder', ''),
                attributes = {},
                )
        for key, value in self._ansible.params.iteritems():
            if self._optional_attr(key) and value is not None:
                request['attributes'][key] = self._ansible.params[key]

        self._query('add_host', request)

    def _optional_attr(self, key):
        if key in [
                'alias',
                'address_family',
                'addressv4',
                'addressv6',
                'snmp',
                'agent',
                'parents',
                ]:
            return True
        return False

    def edit(self):
        return 0, "Edited host"


    def _move(self):
        return True


    def delete(self):
        return self._query('delete_host', {'hostname': self._ansible.params['name']})


def main():
    result = {}
    args = dict(
            # Required
            url = dict(type='str', required=True),
            user = dict(type='str', required=True),
            password = dict(type='str', required=True, no_log=True),
            name = dict(type='str', required=True),
            # Optional
            alias = dict(type='str',),
            folder = dict(type='str',),
            address_family = dict(type='str', choices=['ipv4','ipv6','all','no']),
            addressv4 = dict(type='str'),
            addressv6 = dict(type='str'),
            snmp = dict(type='str', choices=['snmpv1', 'snmpv2/3', 'no']),
            agent = dict(type='str', choices=['agent', 'datasources', 'all', 'no']),
            parents = dict(type='list'),
            # Meta
            state = dict(type='str', default='present', choices=['present', 'absent']),
            validate_certs = dict(type='str', default='yes', choices=['yes', 'no']),
            )

    ansible = AnsibleModule(
            argument_spec=args,
            supports_check_mode=False
            )

    url= '%s/check_mk/webapi.py' % ansible.params['url']
    payload = dict(
            request_format = 'python',
            output_format = 'python',
            _username = ansible.params['user'],
            _secret = ansible.params['password'],
            )

    cmk = cmk_host(url, payload, ansible)
    cmk.get()

    if ansible.params['state'] == 'present':
        if cmk.result_code == 1:
            cmk.add()
            changed = True
        elif cmk.config_changed():
            cmk.edit()
            changed = True
    elif ansible.params['state'] == 'absent':
        if cmk.result_code == 0:
            cmk.delete()
            changed= True


    result = dict(
            changed=changed,
            action=cmk._payload['action'],
            request=cmk._payload['request'],
            result=cmk.result,
            result_code=cmk.result_code,
            )
    ansible.exit_json(**result)

if __name__ == '__main__':
    main()
