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

# Import from itools
from itools.gettext import MSG
from itools.web import ERROR

# Import from ikaaro
from ikaaro.config_common import NewResource_Local
from ikaaro.fields import Char_Field, Integer_Field
from ikaaro.folder import Folder

# Import from agitools
from agitools.fields import File_Field

# Import from goodforms
from application_views import Application_Edit, Application_Export, Applications_View
from application_views import Application_NewInstance, Application_View, Application_EditODS
from application_views import Application_RedirectToForm
from controls import Controls
from datatypes import Subscription_Field
from form import Form
from formpage import FormPage
from rw import get_reader_and_cls
from schema import Schema
from utils import FormatError
from workflow import EMPTY, PENDING, FINISHED


ERR_NOT_ODS_XLS = ERROR(u"Not an ODS or XLS file.")
ERR_WRONG_NUMBER_COLUMNS = ERROR(u'In the "{name}" sheet, wrong number of columns. Do you use the latest template?')
ERR_FIRST_PAGE = ERROR(u'First form page must be named "A", not "{page}".')
ERR_PAGE_NAME = ERROR(u'In the "{name}" sheet, page "{page}" is not related to any variable in the schema.')


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
    class_views =  ['view', 'show', 'edit', 'edit_ods', 'export']

    # Configuration obsolete ?
    allowed_users = 10
    default_form = '0'

    # Configuration
    schema_class = Schema
    controls_class = Controls

    # Fields
    max_users = Integer_Field(default=allowed_users)
    data = File_Field(title=MSG(u'Fichier ODS'), multilingual=False, required=True)
    subscription = Subscription_Field


    def _load_from_file(self, data, context):
        filename, mimetype, body = data
        reader, cls = get_reader_and_cls(mimetype)
        if reader is None:
            raise FormatError(ERR_NOT_ODS_XLS)
        # Save ODS file
        kw = {'data': body,
              'filename': filename,
              'title': {'en': u"Parameters"}}
        self.make_resource('parameters', cls, **kw)
        # Split tables
        document = reader(body)
        tables = iter(document.get_tables())
        # Controls and Schema
        for name, title, cls in [
                ('schema', u"Schema", self.schema_class),
                ('controls', u"Controls", self.controls_class)]:
            table = tables.next()
            table.rstrip(aggressive=True)
            field = cls.get_field('data')
            if table.get_width() != len(field.class_handler.columns):
                error = ERR_WRONG_NUMBER_COLUMNS.gettext(name=table.get_name())
                raise FormatError(error)
            # Create schema or controls
            data = table.to_csv()
            kw = {'title': {'en': title},
                  'data': data}
            r = self.make_resource(name, cls, **kw)
            r._load_from_csv()
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
                raise FormatError, ERR_FIRST_PAGE.gettext(page=page_number)
            if page_number not in pages:
                raise FormatError, ERR_PAGE_NAME.gettext(name=name, page=page_number)
            # Name
            name = 'page' + page_number.lower().encode()
            # Title
            if title is None:
                # Find a "*Title"
                title = find_title(table)
                if title is None:
                    title = u"Page {0}".format(page_number)
            kw = {'title': {'en': title},
                  'data': table.to_csv()}
            self.make_resource(name, FormPage, **kw)
        # Initial form
        name = self.default_form
        if self.get_resource(name, soft=True) is None:
            self.make_resource(name, Form)
        return False


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
        stats['available_users'] = self.get_value('max_users')
        stats['registered_users'] = 0
        stats['unconfirmed_users'] = 0
        stats['empty_forms'] = 0
        stats['pending_forms'] = 0
        stats['finished_forms'] = 0
        users = self.get_resource('/users')
        for form in self.get_forms():
            stats['registered_users'] += 1
            user = users.get_resource(form.name)
            if user.get_value('password') is None:
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


    def get_admin_url(self, context):
        base_url = context.uri.resolve(self.abspath)
        return base_url.resolve2(';view')


    def get_spread_url(self, context, email=None):
        base_url = context.uri.resolve(self.abspath)
        spread_url = base_url.resolve2(';login')
        if email is not None:
            spread_url.query['username'] = email
        return spread_url



    # Views
    view = Application_View()
    new_instance = Application_NewInstance()
    edit = Application_Edit()
    edit_ods = Application_EditODS()
    export = Application_Export()
    show = Application_RedirectToForm()



class Applications(Folder):

    class_id = 'applications'
    class_title = MSG(u"Formulaires")
    class_views = ['view', 'new_resource']
    class_icon_name = 'applications'
    class_icon_css = 'fa-pencil'

    def get_document_types(self):
        return [Application]

    # Views
    view = Applications_View
    new_resource = NewResource_Local(title=MSG(u'Create an application'))
