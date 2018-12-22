# -*- coding: UTF-8 -*-
# Copyright (C) 2018 Taverne Sylvain <taverne.sylvain@gmail.com>
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

# Import from itools
from itools.gettext import MSG
from itools.web import ERROR

# Import from ikaaro
from ikaaro.folder import Folder

# Import from goodforms
from controls import Controls
from formpage import FormPages, FormPage
from rw import get_reader_and_cls
from schema import Schema
from utils import FormatError
from utils import IconsView


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




class FormModel(Folder):

    class_id = 'form-model'
    class_title = MSG(u"Model")
    class_views = ['view']
    class_icon_css = 'fa-cog'

    def load_ods_file(self, context):
        errors = []
        application = self.parent
        mimetype = application.get_value('mimetype')
        reader, cls = get_reader_and_cls(mimetype)
        if reader is None:
            raise FormatError(ERR_NOT_ODS_XLS)
        # Split tables
        handler = application.get_value('data')
        data = handler.to_str()
        document = reader(data)
        tables = iter(document.get_tables())
        # Controls and Schema
        for name, title, cls in [
                ('schema', u"Schema", Schema),
                ('controls', u"Controls", Controls)]:
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
            errors.extend(r.get_errors())
            # TODO Will raise on errors: I prefer load CSV,
            # do not allow to fill forms but to display all errors
            #r._load_from_csv()
        if errors:
            return errors
        schema_resource = self.get_resource('schema')
        schema, pages = schema_resource.get_schema_pages()
        # Pages
        pages_container = self.make_resource('pages', FormPages)
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
            pages_container.make_resource(name, FormPage, **kw)
        # Ok
        return errors


    # Views
    view = IconsView
