# -*- coding: UTF-8 -*-
# Copyright (C) 2010 Hervé Cauwelier <herve@itaapy.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.

# Import from standard library
import traceback

# Import from itools
from itools.core import merge_dicts, get_abspath, freeze
from itools.datatypes import String, XMLContent
from itools.fs import FileName
from itools.gettext import MSG
from itools.html import HTMLParser

# Import from ikaaro
from ikaaro.autoedit import AutoEdit
from ikaaro.fields import Char_Field, Text_Field
from ikaaro.file import Image
from ikaaro.root import Root as BaseRoot
from ikaaro.widgets import RTEWidget, TextWidget

# Import from goodforms
from base_views import  LoginView
from products import Products
from root_views import Root_View, Root_Show, Root_Contact
from root_views import Root_ViewAdmin
from root_views import Root_ShowAllWorkgroups, Root_ShowAllApplications
from utils import is_debug
from workgroup import Workgroup


class Root(BaseRoot):

    class_id = 'goodforms'
    class_skin = 'goodforms'
    class_version = '20120411'
    class_views = BaseRoot.class_views + ['show']

    # Configuration
    __fixed_handlers__ = BaseRoot.__fixed_handlers__ + ['shop', 'products']

    # Fields
    homepage = Char_Field
    slogan =  Text_Field
    recaptcha_private_key = Char_Field
    recaptcha_public_key = Char_Field
    recaptcha_whitelist = Char_Field



    #def init_resource(self, email, password, admins=('0',)):
    #    super(Root, self).init_resource(email, password)
    #    self.set_property('title', u"GoodForms", language='en')
    #    #value = self.class_schema['homepage'].decode("""
    #    #        <h2>Welcome to GoodForms!</h2>
    #    #        <ul>
    #    #          <li><a href=";new_resource?type=Workgroup">Create a
    #    #          workgroup</a>;</li>
    #    #          <li><a href=";show">Your workgroups (authenticated users
    #    #          only)</a>.</li>
    #    #        </ul>""")
    #    #self.set_property('homepage', value, language='en')
    #    # Laisse voir le nom du website
    #    theme = self.get_resource('theme')
    #    theme.set_property('logo', None)
    #    # Products
    #    self.make_resource('products', Products)
    #    # Favicon à utiliser partout
    #    filename = 'itaapy-favicon.ico'
    #    with open(get_abspath('ui/' + filename)) as file:
    #        body = file.read()
    #    name, extension, _ = FileName.decode(filename)
    #    theme.make_resource(name, Image, body=body, filename=filename,
    #            extension=extension, state='public', format='image/x-icon')
    #    theme.set_property('favicon', name)


    def get_user_role(self, name):
        return u'XXX'


    def get_document_types(self):
        return super(Root, self).get_document_types() + [Workgroup]


    def get_page_title(self):
        return None


    def is_allowed_to_view(self, user, resource):
        # FIXME
        return True


    def is_allowed_to_add(self, user, resource, class_id=None):
        # FIXME
        return True

    def is_authenticated(self, user, resource):
        return user is not None
    # Views
    view = Root_View()
    view_admin = Root_ViewAdmin()
    _fields = ['title']
    edit = AutoEdit(fields=_fields)
    show = Root_Show()
    show_all_workgroups = Root_ShowAllWorkgroups()
    show_all_applications = Root_ShowAllApplications()
    contact = Root_Contact()
    # Security
    login = LoginView()
    unauthorized = LoginView()
