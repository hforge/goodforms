Goodforms is a community-driven free software solution to easily generate and work with complex online forms.


Dependencies
=====================

  - itools (V 0.78)
  - ikaaro (V 0.68)
  - lpod-python (master)

Installation
=====================

Install via git repository:

    $ python setup.py -r requirements.txt
    $ python setup.py install


Create a new instance
=======================

Initialize instance:

    $ icms-init.py -w yourpassword -e email@example.com www.goodforms.localhosh

Start instance:

    $ icms-start.py www.goodforms.localhost

Test goodform in Firefox:

    $ firefox http://localhost:8080/
