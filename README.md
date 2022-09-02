# Ansible roles and modules

# Deprecation Warning!
We are deprecating this project in favor of our very own official
[Ansible Collection](https://github.com/tribe29/ansible-collection-tribe29.checkmk). We are confident, that it will
deliver just as much value, as this project, while being up-to-date
with the Ansible ecosystem.  
So what does that mean? We will leave this repository open until the end
of October 2022 and archive it then.  
See you on the other side!

# Original README

check**mk** already provides the needed APIs to automate the basic
configuration of your monitoring. With this project we want to create and
share roles and modules of ansible to simplify your first steps with
ansible in combination with check**mk**.

## Getting started

At the beginning this project contains a simple **playbook** as an
example, a **hosts.ini** and the needed roles to execute this playbook.
Things to do for the first test run:
* In each role: adjust the defaults, if needed. At the moment you still
  need to set the check**mk** version manually. 
* In the host.ini: Fill it with your hosts and remove the examples
* In the playbook: Find the tags to run the roles you want

Execute your playbook with a bunch of testhosts:

    ansible-playbook -i hosts.ini ansible-example.yml --tags all

## Further information to each role

* [Installation of check**mk** agent](./README_cmk_host_agent.md)
* [Installation of check**mk** agent plugins](./README_cmk_host_plugins.md)
* [Registration of hosts in check**mk**](./README_cmk_host_registration.md)
