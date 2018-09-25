# -*- coding: UTF-8 -*-
# Copyright (C) 2005  <jdavid@favela.(none)>
# Copyright (C) 2006 J. David Ibanez <jdavid@itaapy.com>
# Copyright (C) 2006 luis <luis@lucifer.localdomain>
# Copyright (C) 2006-2008, 2010 Hervé Cauwelier <herve@itaapy.com>
# Copyright (C) 2008 Henry Obein <henry@itaapy.com>
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

# Import from itools
from itools.core import freeze
from itools.csv import Table as TableFile, parse
from itools.datatypes import Enumerate, Unicode
from itools.gettext import MSG
from itools.web import ERROR

# Import from ikaaro
from ikaaro.table import Table
from ikaaro.table_views import Table_View

# Import from goodforms
from schema import FormatError, Variable, Expression


ERR_EMPTY_TITLE = ERROR(u'In controls, line {line}, title is missing.')
ERR_EMPTY_EXPRESSION = ERROR(u'In controls, line {line}, expression is '
        u'missing.')
ERR_BAD_EXPRESSION = ERROR(u'In controls, line {line}, syntax error in '
        u'expression: {err}')
ERR_BAD_LEVEL = ERROR(u'In controls, line {line}, unexpected level '
        u'"{level}".')
ERR_EMPTY_VARIABLE = ERROR(u'In controls, line {line}, main variable is '
        u'missing.')


class ControlLevel(Enumerate):
    options = [
        {'name': '0', 'value': u"Informative"},
        {'name': '1', 'value': u"Warning"},
        {'name': '2', 'value': u"Error"}]


    @staticmethod
    def decode(data):
        data = data.strip()
        return Enumerate.decode(data)



class ControlsHandler(TableFile):
    record_properties = {
        'number': Unicode(mandatory=True, title=MSG(u"Number")),
        'title': Unicode(mandatory=True, title=MSG(u"Title")),
        'expression': Expression(mandatory=True, title=MSG(u"Expression")),
        'level': ControlLevel(mandatory=True, title=MSG(u"Level")),
        'variable': Variable(mandatory=True, title=MSG(u"Main Variable"))}



class Controls(Table):
    class_id = 'Controls'
    class_title = MSG(u"Controls")
    class_handler = ControlsHandler
    class_icon16 = 'icons/16x16/excel.png'
    class_icon48 = 'icons/48x48/excel.png'

    # To import from CSV
    columns = ['number', 'title', 'expression', 'level', 'variable']

    # Views
    view = Table_View(table_actions=freeze([]))
    add_record = None
    edit_record = None
    edit = None


    def _load_from_csv(self, body, namespace, skip_header=True):
        handler = self.handler
        # Consistency check
        # Starting from 1
        lineno = 2
        for line in parse(body, self.columns, handler.record_properties,
                skip_header=skip_header):
            record = {}
            for index, key in enumerate(self.columns):
                record[key] = line[index]
            # Title
            title = record['title'] = record['title'].strip()
            if not title:
                raise FormatError, ERR_EMPTY_TITLE(line=lineno)
            # Expression
            expression = record['expression']
            if not expression:
                raise FormatError, ERR_EMPTY_EXPRESSION(line=lineno)
            try:
                Expression.is_valid(expression, namespace)
            except Exception, err:
                raise FormatError, ERR_BAD_EXPRESSION(line=lineno,
                        err=err)
            # Level
            level = record['level']
            if not ControlLevel.is_valid(level):
                raise FormatError, ERR_BAD_LEVEL(line=lineno,
                        level=level)
            # Variable
            variable = record['variable']
            if not variable:
                raise FormatError, ERR_EMPTY_VARIABLE(line=lineno)
            handler.add_record(record)
            lineno += 1


    def init_resource(self, body=None, filename=None, extension=None,
            skip_header=True, **kw):
        proxy = super(Controls, self)
        proxy.init_resource(filename=filename, extension=extension, **kw)
        schema_resource = self.parent.get_resource('schema')
        schema, pages = schema_resource.get_schema_pages()
        namespace = {}
        for key in schema:
            namespace[key] = 0
        self._load_from_csv(body, namespace=namespace,
                skip_header=skip_header)


    def get_controls(self):
        handler = self.handler
        get_record_value = handler.get_record_value
        for record in handler.get_records():
            number = get_record_value(record, 'number')
            title = get_record_value(record, 'title')
            expr = get_record_value(record, 'expression')
            level = get_record_value(record, 'level')
            variable = get_record_value(record, 'variable')
            page = variable[0]
            yield (number, title, expr, level, page, variable)
