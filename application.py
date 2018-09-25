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
from copy import deepcopy

# Import from itools
from itools.core import merge_dicts, freeze
from itools.datatypes import String, DateTime, Integer
from itools.gettext import MSG
from itools.uri import Path
from itools.web import ERROR, get_context

# Import from ikaaro
from ikaaro.fields import Char_Field, Integer_Field
from ikaaro.folder import Folder

# Import from goodforms
from application_views import Application_Edit, Application_Export
from application_views import Application_NewInstance, Application_View
from application_views import Application_RedirectToForm, Application_Menu
from application_views import Application_Register, Application_Login
from application_views import Application_NewOrder
from controls import Controls
from datatypes import Subscription
from emails import email_credit_alert
from form import Form
from formpage import FormPage
from rw import get_reader_and_cls
from schema import Schema, FormatError
from workflow import EMPTY, PENDING, FINISHED


ERR_NOT_ODS_XLS = ERROR(u"Not an ODS or XLS file.")
ERR_WRONG_NUMBER_COLUMNS = ERROR(u'In the "{name}" sheet, wrong number of '
        u'columns. Do you use the latest template?')
ERR_FIRST_PAGE = ERROR(u'First form page must be named "A", not '
        u'"{page}".')
ERR_PAGE_NAME = ERROR(u'In the "{name}" sheet, page "{page}" is not '
        u'related to any variable in the schema.')


def find_title(table):
    for values in table.iter_values():
        for value in values:
            value = value.strip() if value is not None else u""
            if value.startswith(u'**'):
                continue
            elif value.startswith(u"*"):
                return value[1:].strip()
    return None


class Application(Folder):

    class_id = 'Application'
    class_title = MSG(u"Collection Application")
    class_description = MSG(u"Create from an OpenDocument Spreadsheet file")
    class_icon16 = 'icons/16x16/tasks.png'
    class_icon48 = 'icons/48x48/tasks.png'
    class_views = Folder.class_views + ['show']

    # Configuration
    allowed_users = 10
    schema_class = Schema
    controls_class = Controls
    default_form = '0'

    # Fields
    author = Char_Field(indexed=True, stored=True)
    max_users=  Integer_Field(default=allowed_users)
    subscription = Subscription



    def _load_from_file(self, file, context):
        filename, mimetype, body = file
        reader, cls = get_reader_and_cls(mimetype)
        if reader is None:
            raise FormatError, ERR_NOT_ODS_XLS
        # Save file used
        self.make_resource('parameters', cls, body=body, filename=filename,
                title={'en': u"Parameters"}, state='public')
        # Split tables
        document = reader(body)
        tables = iter(document.get_tables())
        # Controls and Schema
        for name, title, cls in [
                ('schema', u"Schema", self.schema_class),
                ('controls', u"Controls", self.controls_class)]:
            table = tables.next()
            table.rstrip(aggressive=True)
            if table.get_width() != len(cls.columns):
                raise FormatError, ERR_WRONG_NUMBER_COLUMNS(
                        name=table.get_name())
            self.make_resource(name, cls, title={'en': title},
                    # cls va transformer le CSV en table
                    body=table.to_csv())
        schema_resource = self.get_resource('schema')
        schema, pages = schema_resource.get_schema_pages()
        # Pages
        for i, table in enumerate(tables):
            table.rstrip(aggressive=True)
            name = table.get_name().split(None, 1)
            # Page number
            if len(name) == 1:
                page_number = name[0]
                title = None
            else:
                page_number, title = name
            if i == 0 and page_number != 'A':
                raise FormatError, ERR_FIRST_PAGE(page=page_number)
            if page_number not in pages:
                raise FormatError, ERR_PAGE_NAME(name=name, page=page_number)
            # Name
            name = 'page' + page_number.lower().encode()
            # Title
            if title is None:
                # Find a "*Title"
                title = find_title(table)
                if title is None:
                    title = u"Page {0}".format(page_number)
            self.make_resource(name, FormPage, title={'en': title},
                    body=table.to_csv())
        # Initial form
        name = self.default_form
        if self.get_resource(name, soft=True) is None:
            self.make_resource(name, Form)
        return False


    def get_logo_icon(self, size=48):
        return self.get_class_icon(size=size)


    def get_form(self):
        return self.get_resource(self.default_form, soft=True)


    def get_forms(self):
        for form in self.search_resources(cls=Form):
            if form.name != self.default_form:
                yield form


    def get_n_forms(self):
        return len(list(self.get_forms()))


    def get_stats(self):
        stats = {}
        stats['available_users'] = self.get_property('max_users')
        stats['registered_users'] = 0
        stats['unconfirmed_users'] = 0
        stats['empty_forms'] = 0
        stats['pending_forms'] = 0
        stats['finished_forms'] = 0
        users = self.get_resource('/users')
        for form in self.get_forms():
            stats['registered_users'] += 1
            user = users.get_resource(form.name)
            if user.get_property('password') is None:
                stats['unconfirmed_users'] += 1
            else:
                state = form.get_workflow_state()
                if state == EMPTY:
                    stats['empty_forms'] += 1
                elif state == PENDING:
                    stats['pending_forms'] += 1
                elif state == FINISHED:
                    stats['finished_forms'] += 1
        return stats


    def get_param_folder(self):
        return self


    def get_allowed_users(self):
        max_users = self.get_value('max_users')
        if not max_users:
            return float('inf')
        n_forms = self.get_n_forms()
        return (max_users - n_forms)


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
        site_root = self.get_site_root()
        username = user.name
        # Give the role "guests" to see public resources (logo, etc.)
        if (site_root.get_user_role(username) is None
                # Except to top-level admins
                and not site_root.is_admin(user, self)):
            site_root.set_user_role(username, 'guests')
        # Add the form
        if self.get_resource(username, soft=True) is None:
            self.make_resource(username, Form,
                    title={'en': user.get_title()})
        # Send credit alert
        self.send_credit_alert()


    def send_credit_alert(self):
        """
        Send an alert to workgroup administrators
        if max_users-nb_forms = 0 or 5 or 10 or 15 or 20
        """
        # Check if we have to send an alert ?
        nb_forms = self.get_n_forms()
        max_users = self.get_property('max_users')
        if (max_users - nb_forms) not in (0, 5, 10, 15, 20):
            return
        # Build alert kw
        context = get_context()
        root = self.get_root()
        workgroup = self.parent
        order_uri = deepcopy(context.uri)
        order_uri.path = Path('%s/;order' % root.get_pathto(self))
        kw = {'application_title': self.get_title(),
              'workgroup_title': workgroup.get_title(),
              'nb_forms': nb_forms,
              'max_users': max_users,
              'remaining_users': max_users - nb_forms,
              'order_uri': str(order_uri)}
        # Send Alert to workgroup administrators
        root = self.get_root()
        for user in workgroup.get_workgroup_administrators():
            email = user.get_property('email')
            kw['user_title'] = user.get_title()
            subject = email_credit_alert['subject'].gettext(**kw)
            text = email_credit_alert['text'].gettext(**kw)
            root.send_email(email, subject, text=text)




    # Views
    new_instance = Application_NewInstance()
    menu = Application_Menu()
    view = Application_View()
    edit = Application_Edit()
    export = Application_Export()
    register = Application_Register()
    login = Application_Login()
    show = Application_RedirectToForm()
    order = Application_NewOrder()
