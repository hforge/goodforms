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
from ikaaro.autoform import XHTMLBody, RTEWidget, TextWidget
from ikaaro.config import get_config
from ikaaro.datatypes import Multilingual
from ikaaro.file import Image
from ikaaro.root import Root as BaseRoot
from ikaaro.workflow import WorkflowAware

# Import from itws
from itws.shop import Shop

# Import from goodforms
from base_views import AutomaticEditView, LoginView
from products import Products
from root_views import Root_View, Root_Show, Root_Contact
from root_views import Root_EditContactOptions, Root_ViewAdmin
from root_views import Root_ShowAllWorkgroups, Root_ShowAllApplications
from utils import is_debug
from workgroup import Workgroup


class Root(BaseRoot):
    class_id = 'goodforms'
    class_schema = freeze(merge_dicts(
        BaseRoot.class_schema,
        homepage=XHTMLBody(source='metadata', multilingual=True,
                           parameters_schema = {'lang': String}),
        slogan=Multilingual(source='metadata'),
        recaptcha_private_key=String(source='metadata'),
        recaptcha_public_key=String(source='metadata'),
        recaptcha_whitelist=String(source='metadata', multiple=True,
            default=['127.0.0.1'])))
    class_skin = 'ui/goodforms'
    class_version = '20120411'
    class_views = BaseRoot.class_views + ['show']

    __fixed_handlers__ = BaseRoot.__fixed_handlers__ + ['shop', 'products']

    edit_schema = freeze({
        'homepage': XHTMLBody(multilingual=True),
        'slogan': Multilingual})
    edit_widgets = freeze([
        TextWidget('slogan', title=MSG(u'Slogan')),
        RTEWidget('homepage', title=MSG(u'Homepage'))])

    # Views
    view = Root_View()
    view_admin = Root_ViewAdmin()
    edit = AutomaticEditView()
    show = Root_Show()
    show_all_workgroups = Root_ShowAllWorkgroups()
    show_all_applications = Root_ShowAllApplications()
    contact = Root_Contact()
    edit_contact_options = Root_EditContactOptions()
    # Security
    login = LoginView()
    unauthorized = LoginView()


    def init_resource(self, email, password, admins=('0',)):
        super(Root, self).init_resource(email, password, admins=admins)
        self.set_property('title', u"GoodForms", language='en')
        value = self.class_schema['homepage'].decode("""
                <h2>Welcome to GoodForms!</h2>
                <ul>
                  <li><a href=";new_resource?type=Workgroup">Create a
                  workgroup</a>;</li>
                  <li><a href=";show">Your workgroups (authenticated users
                  only)</a>.</li>
                </ul>""")
        self.set_property('homepage', value, language='en')
        # Laisse voir le nom du website
        theme = self.get_resource('theme')
        theme.set_property('logo', None)
        # Products
        self.make_resource('products', Products)
        # Shop
        shop = self.make_resource('shop', Shop)
        paybox = shop.get_resource('payments/paybox')
        msg = u"""
          <p>Votre règlement est en cours de validation par nos équipes.
          Vous allez recevoir un email dès que celui-ci aura été validé.</p>
          <a href="../">Voir ma commande</a>
        """
        msg = msg.encode('utf-8').strip()
        msg = HTMLParser(XMLContent.decode(msg))
        paybox.set_property('payment_end_msg', msg, language='fr')
        # Favicon à utiliser partout
        filename = 'itaapy-favicon.ico'
        with open(get_abspath('ui/' + filename)) as file:
            body = file.read()
        name, extension, _ = FileName.decode(filename)
        theme.make_resource(name, Image, body=body, filename=filename,
                extension=extension, state='public', format='image/x-icon')
        theme.set_property('favicon', name)


    def get_document_types(self):
        return super(Root, self).get_document_types() + [Workgroup]


    def get_page_title(self):
        return None


    def is_allowed_to_view(self, user, resource):
        if isinstance(resource, WorkflowAware):
            state = resource.get_workflow_state()
            if state == 'public':
                return True
            return self.is_allowed_to_edit(user, resource)
        return True


    def is_allowed_to_add(self, user, resource, class_id=None):
        # Allow anonymous to create workgroups
        if class_id == Workgroup.class_id:
            return True
        return super(Root, self).is_allowed_to_add(user, resource)


    def internal_server_error(self, context):
        if not is_debug(context):
            # We send an email to administrators
            config = get_config(context.server.target)
            email = config.get_value('admin-email')
            if email is None:
                email = config.get_value('smtp-from')
            subject = u"[GoodForms] Internal server error"
            text = u"%s\n\n%s" % (context.uri, traceback.format_exc())
            self.send_email(email, subject, text=text)
        return super(Root, self).internal_server_error(context)


    def update_20120409(self):
        shop = self.make_resource('shop', Shop)
        paybox = shop.get_resource('payments/paybox')
        msg = u"""
          <p>Votre règlement est en cours de validation par nos équipes.
          Vous allez recevoir un email dès que celui-ci aura été validé.</p>
          <a href="../">Voir ma commande</a>
        """
        msg = msg.encode('utf-8').strip()
        msg = HTMLParser(XMLContent.decode(msg))
        paybox.set_property('payment_end_msg', msg, language='fr')


    def update_20120410(self):
        self.make_resource('products', Products)
