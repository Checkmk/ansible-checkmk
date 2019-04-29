# Registration of a host on a checkmk site

This role ensures that a host is present on a check**mk** site. It adds
a host if it is not present or readds the host, if it was deleted or
modified. Additionally there will be a service discovery and the
activation of changes. 

This role currently covers:
* Adding or readding a host into a check**mk** site
* ~~Do a service discovery for this host~~
* ~~Activate the changes on the site~~

## Variables that may need manual interaction

* `cmk_site_url: "https://myserver.corp.org/mysite"`
* `cmk_site_default_folder: "automation"`

## Wishlist of features that may be added

* Support for more attributes
* Support for cluster hosts?
* ???
