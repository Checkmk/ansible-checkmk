#!/usr/bin/python
# -*- encoding: utf-8; py-indent-offset: 4 -*-

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '0.1'}

DOCUMENTATION = '''
module: checkmk_host

short_description: Managing hosts in checkMK

version_added: "0.1"

description:
    - "With the C(checkmk_host) module allows to add/edit/delete hosts"

author: "Marcel Arentz (@ma@mathias-kettner.de)"

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
  checkmk_host:
    url: https://monitoring.example.org/mysite
    user: myuser
    password: mypassword
    name: myhost1

- name: Add host with specific folder and with explcit ip address
  checkmk_host:
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
from ansible.module_utils.checkmk_api import Hosts, Services, Changes

class CallHost:
    def __init__(self, session):
        self.session = session
        self.hostname = session.hostname

        self.is_present, self.data = self._get(1)


    def _get(self, effective):
        host = self.session.get(effective_attributes=effective)
        if isinstance(host['result'], dict):
            return True, host['result']
        else:
            return False, host['result']


    def add(self, payload):
        result = self.session.add(payload=payload)
        return True, result['result']


    def edit(self, request):
        diff = False
        payload = request.copy()
        if payload['folder'] != self.data['path']:
            self.delete()
            changed, result = self.add(payload=payload)
            return changed, result
        payload.pop('folder')

        needed_attr = payload['attributes']
        _is_present, existing_attr = self._get(0)
        existing_attr = existing_attr.get('attributes', {})
        unset_attr = []
        if not needed_attr:
            if not existing_attr:
                return False, None

            for key in existing_attr:
                unset_attr.append(key)

            payload['unset_attributes'] = unset_attr
            return True, self.session.edit(payload=payload)['result']
        else:
            if not existing_attr:
                return True, self.session.edit(payload=payload)['result']

            # We need to figure what to do with every custom key
            for key, value in existing_attr.iteritems():
                if key not in needed_attr:
                    unset_attr.append(key)
                elif value != needed_attr[key]:
                    diff = True

            if len(unset_attr) > 0:
                payload['unset_attributes'] = unset_attr
                return True, self.session.edit(payload=payload)['result']
            if diff:
                return True, self.session.edit(payload=payload)['result']
            return False, None


    def delete(self):
        result = self.session.delete(payload={'hostname': self.hostname})
        return True, result['result']


def main():
    args = dict(
        # Required
        url=dict(type='str', required=True),
        user=dict(type='str', required=True),
        password=dict(type='str', required=True, no_log=True),
        name=dict(type='str', required=True),
        # Optional
        attributes=dict(type='dict', default={}),
        folder=dict(type='str', default=''),
        validate_certs=dict(type='str', default='yes', choices=['yes', 'no']),
        discover_services=dict(type='str', default='no', choices=['no', 'refresh']),
        activate_changes=dict(type='str', default='no', choices=['yes', 'no']),
        # Meta
        state=dict(type='str', default='present', choices=['present', 'absent']),
        )

    ansible = AnsibleModule(
        argument_spec=args,
        supports_check_mode=False
        )

    hostname = ansible.params['name']
    state = ansible.params['state']
    discover = ansible.params['discover_services']
    activate = ansible.params['activate_changes']

    host = CallHost(Hosts(
        ansible.params['url'],
        ansible.params['user'],
        ansible.params['password'],
        verify=ansible.params['validate_certs'],
        hostname=hostname,))

    payload = dict(
        hostname=hostname,
        folder=ansible.params['folder'],
        attributes=ansible.params['attributes']
        )

    if state == 'present' and not host.is_present:
        changed, result = host.add(payload)
    elif state == 'present':
        changed, result = host.edit(payload)
    elif state == 'absent' and host.is_present:
        changed, result = host.delete()
    elif state == 'absent':
        changed = False
        result = None

    if isinstance(result, str):
        if 'exception' in result:
            ansible.fail_json(msg='Failed to work on %s: %s' % (hostname, result),
                              request=payload,
                              orig_data=host.data)

    ansible_result = dict(
        changed=changed,
        request=payload,
        result=result,
        )

    if discover != 'no' and changed == True:
        service = Services(
            ansible.params['url'],
            ansible.params['user'],
            ansible.params['password'],
            verify=ansible.params['validate_certs'],
            hostname=hostname)
        discovery = service.discover(mode=discover)
        ansible_result['service_discovery'] = dict(
            result=discovery['result'],
            status=discovery['result_code'],
            )

    if activate != 'no' and changed == True:
        changes = Changes(
            ansible.params['url'],
            ansible.params['user'],
            ansible.params['password'],
            verify=ansible.params['validate_certs'])
        activation = changes.activate(allow_foreign_changes=1)
        ansible_result['activate_changes'] = dict(
            result=activation['result'],
            status=activation['result_code'],
            )

    ansible_result['hostname'] = hostname
    ansible.exit_json(**ansible_result)

if __name__ == '__main__':
    main()
