Dependencies
=====================

  - itools (V 0.62)
  - ikaaro (V 0.62)
  - lpod-python (V master)
  - itws (V 1.3)

Installation
=====================

 $ python setup.py install


Create a new instance
=======================

Initialize instance:

  $ icms-init.py goodforms.localhost

Set goodforms as a module

  $ vi goodforms.localhost/config.conf

    > + modules = goodforms
    > - modules =

Start instance:

  $ icms-start.py goodforms.localhost

Open firefox

  $ firefox http://localhost:8080/

Add a website

  $ firefox http://localhost:8080/;new_resource?type=WebSite

Your website is the demo website.
