# -*- coding: UTF-8 -*-
# Copyright (C) 2010 Hervé Cauwelier <herve@itaapy.com>
# Copyright (C) 2018 Nicolas Deram <nderam@gmail.com>
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

# Import from itools
from itools.database import AndQuery, PhraseQuery
from itools.gettext import MSG
from itools.web import get_context

# Import from ikaaro
from ikaaro.config_common import NewResource_Local
from ikaaro.fields import File_Field, Char_Field
from ikaaro.folder import Folder
from ikaaro.utils import get_base_path_query

# Import from goodforms
from application_views import Application_Edit, Applications_View
from application_views import Application_NewInstance, Application_EditODS
from application_views import Application_Register
from datatypes import Subscription_Field
from form import Form, Forms
from form_views import Forms_View
from model import FormModel
from utils import IconsView
from workflow import NOT_REGISTERED, EMPTY, PENDING, FINISHED


class Application(Folder):

    class_id = 'application'
    class_title = MSG(u"Collection Application")
    class_description = MSG(u"Create from an OpenDocument Spreadsheet file")
    class_views =  ['view_admin', 'edit', 'edit_ods', 'register', 'view']

    # FIXME Configuration obsolete ?
    allowed_users = 10

    # Fields
    subscription = Subscription_Field(required=True)
    data = File_Field(title=MSG(u'ODS file'), multilingual=False, required=True)
    filename = Char_Field()
    mimetype = Char_Field()


    def init_resource(self, *args, **kw):
        proxy = super(Application, self)
        proxy.init_resource(*args, **kw)
        # Initial forms answers containers
        self.make_resource('forms', Forms)


    def load_ods_file(self, data, context):
        if self.get_resource('model', soft=True):
            self.del_resource('model')
            context.database.save_changes()
        # Create model container
        self.make_resource('model', FormModel)
        model = self.get_resource('model')
        # Save informations
        filename, mimetype, body = data
        self.set_value('data', body)
        self.set_value('filename', filename)
        self.set_value('mimetype', mimetype)
        # Analyse it
        return model.load_ods_file(context)


    def get_form(self):
        # OBSOLETE METHOD FIXME
        raise NotImplementedError


    def search_forms(self):
        query = AndQuery(PhraseQuery('base_classes', 'form'),
                         get_base_path_query(self.abspath))
        return get_context().search(query)


    def get_forms(self):
        return self.search_forms().get_resources()


    def get_n_forms(self):
        return len(self.search_forms())


    def get_stats(self):
        stats = {}
        stats['registered_users'] = 0
        stats['unconfirmed_users'] = 0
        stats['empty_forms'] = 0
        stats['pending_forms'] = 0
        stats['finished_forms'] = 0
        users = self.get_resource('/users')
        for form in self.get_forms():
            stats['registered_users'] += 1
            user = users.get_resource(form.name, soft=True)
            if user is not None:
                if user.get_value('password') is None:
                    stats['unconfirmed_users'] += 1
                else:
                    state = form.get_value('form_state')
                    if state == EMPTY:
                        stats['empty_forms'] += 1
                    elif state == PENDING:
                        stats['pending_forms'] += 1
                    elif state == FINISHED:
                        stats['finished_forms'] += 1
        return stats


    def get_param_folder(self):
        return self


    def get_admin_url(self, context):
        base_url = context.uri.resolve(self.abspath)
        return base_url.resolve2(';view')


    def get_spread_url(self, context, email=None):
        base_url = context.uri.resolve(self.abspath)
        spread_url = base_url.resolve2(';login')
        if email is not None:
            spread_url.query['username'] = email
        return spread_url


    def subscribe_user(self, user):
        root = self.get_resource('/')
        username = user.name
        # Give the role "guests" to see public resources (logo, etc.)
        if (root.get_user_role(username) is None
                # Except to top-level admins
                and not root.is_admin(user, self)):
            root.set_user_role(username, 'guests')
        # Add the form
        if self.get_resource(username, soft=True) is None:
            self.make_resource(username, Form,
                    title={'en': user.get_title()},
                    form_state=NOT_REGISTERED)


    # Views
    view = Forms_View()
    new_instance = Application_NewInstance()
    edit = Application_Edit()
    edit_ods = Application_EditODS()
    view_admin = IconsView()
    register = Application_Register()



class Applications(Folder):

    class_id = 'applications'
    class_title = MSG(u"Forms")
    class_views = ['view', 'new_resource']
    class_icon_name = 'applications'
    class_icon_css = 'fa-pencil-alt'

    def get_document_types(self):
        return [Application]

    # Views
    view = Applications_View()
    new_resource = NewResource_Local(title=MSG(u'Create an application'))
