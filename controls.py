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
from itools.csv import CSVFile
from itools.datatypes import Enumerate, Unicode
from itools.gettext import MSG
from itools.web import ERROR

# Import from ikaaro
from ikaaro.fields import Char_Field, File_Field
from ikaaro.folder import Folder

# Import from goodforms
from schema import Variable, Expression
from utils import FormatError



ERR_EMPTY_TITLE = ERROR(u'In controls, line {line}, title is missing.')
ERR_EMPTY_EXPRESSION = ERROR(u'In controls, line {line}, expression is missing.')
ERR_BAD_EXPRESSION = ERROR(u'In controls, line {line}, syntax error in expression: {err}')
ERR_BAD_LEVEL = ERROR(u'In controls, line {line}, unexpected level "{level}".')
ERR_EMPTY_VARIABLE = ERROR(u'In controls, line {line}, main variable is missing.')


class ControlLevel(Enumerate):

    options = [
        {'name': '0', 'value': u"Informative"},
        {'name': '1', 'value': u"Warning"},
        {'name': '2', 'value': u"Error"}]


    @staticmethod
    def decode(data):
        data = data.strip()
        return Enumerate.decode(data)



class ControlsHandler(CSVFile):

    skip_header = True
    has_header = True
    class_csv_guess = True

    schema = {
        'number': Unicode(mandatory=True, title=MSG(u"Number")),
        'title': Unicode(mandatory=True, title=MSG(u"Title")),
        'expression': Expression(mandatory=True, title=MSG(u"Expression")),
        'level': ControlLevel(mandatory=True, title=MSG(u"Level")),
        'variable': Variable(mandatory=True, title=MSG(u"Main Variable"))}

    columns = ['number', 'title', 'expression', 'level', 'variable']



class Controls(Folder):

    class_id = 'Controls'
    class_title = MSG(u"Controls")
    class_handler = ControlsHandler

    # Fields
    data = File_Field(class_handler=ControlsHandler)
    extension = Char_Field
    filename = Char_Field


    def _load_from_csv(self):
        handler = self.get_value('data')
        # Consistency check
        # Starting from 1
        lineno = 2
        for row in handler.get_rows():
            # Title
            title = row.get_value('title').strip()
            if not title:
                raise FormatError, ERR_EMPTY_TITLE.gettext(line=lineno)
            # Expression
            expression = row.get_value('expression')
            if not expression:
                raise FormatError, ERR_EMPTY_EXPRESSION.gettext(line=lineno)
            try:
                Expression.is_valid(expression, namespace)
            except Exception, err:
                raise FormatError, ERR_BAD_EXPRESSION.gettext(line=lineno, err=err)
            # Level
            level = row.get_value('level')
            if not ControlLevel.is_valid(level):
                raise FormatError, ERR_BAD_LEVEL.gettext(line=lineno, level=level)
            # Variable
            variable = row.get_value('variable')
            if not variable:
                raise FormatError, ERR_EMPTY_VARIABLE.gettext(line=lineno)
            lineno += 1



    def get_controls(self):
        handler = self.get_value('data')
        for row in handler.get_rows():
            number = row.get_value('number')
            title = row.get_value('title')
            expr = row.get_value('expression')
            level = row.get_value('level')
            variable = row.get_value('variable')
            page = variable[0]
            yield (number, title, expr, level, page, variable)
