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

# Import from the Standard Library
import re

# Import from itools
from itools.core import freeze
from itools.csv import Table as TableFile, parse
from itools.datatypes import Enumerate, String, Integer, Boolean, Date
from itools.datatypes import Unicode
from itools.gettext import MSG
from itools.handlers import checkid
from itools.web import ERROR

# Import from ikaaro
from ikaaro.table import Table
from ikaaro.table_views import Table_View

# Import from goodforms
from datatypes import NumInteger, NumDecimal, NumTime, NumShortTime, Text
from datatypes import NumDate, NumShortDate, NumDigit, UnicodeSQL, EnumBoolean, Email, EmailField
from datatypes import SqlEnumerate, Numeric, FileImage
from utils import SI


single_eq = re.compile(ur"""(?<=[^!<>=])[=](?=[^=])""")


ERR_BAD_NAME = ERROR(u'In schema, line {line}, variable "{name}" is '
        u'invalid.')
ERR_DUPLICATE_NAME = ERROR(u'In schema, line {line}, variable "{name}" is '
        u'duplicated.')
ERR_BAD_TYPE = ERROR(u'In schema, line {line}, type "{type}" is '
        u'invalid.')
ERR_BAD_LENGTH = ERROR(u'In schema, line {line}, length "{length}" is '
        u'invalid.')
ERR_MISSING_OPTIONS = ERROR(u'In schema, line {line}, enum options are '
        u'missing.')
ERR_BAD_ENUM_REPR = ERROR(u'In schema, line {line}, enum representation '
        u'"{enum_repr}" is invalid.')
ERR_BAD_DECIMALS = ERROR(u'In schema, line {line}, decimals '
        u'"{decimals}" are invalid.')
ERR_BAD_MANDATORY = ERROR(u'In schema, line {line}, mandatory "{mandatory}" '
        u'is invalid.')
ERR_BAD_SIZE = ERROR(u'In schema, line {line}, size ' u'"{size}" is '
        u'invalid.')
ERR_BAD_DEPENDENCY = ERROR(u'In schema, line {line}, syntax error in '
        u'dependency: {err}')
ERR_BAD_FORMULA = ERROR(u'In schema, line {line}, syntax error in '
        u'formula: {err}')
ERR_NO_FORMULA = ERROR(u'In schema, line {line}, type "{type}" does not '
        u'support formulas.')
ERR_BAD_DEFAULT = ERROR(u'In schema, line {line}, default value '
        u'"{default}" is invalid.')


class FormatError(ValueError):

    def __init__(self, message, *args, **kw):
        message = message.gettext()
        return super(FormatError, self).__init__(message, *args, **kw)



class Variable(String):
    FIELD_PREFIX = '#'


    def decode(cls, data):
        data = data.strip().upper()
        if not data:
            # Turn it into default value at the time of writing
            return None
        if data[0] == cls.FIELD_PREFIX:
            data = data[1:]
        return String.decode(data)


    def is_valid(cls, value):
        return bool(value)


    def get_page_number(cls, value):
        page_number = ''
        for char in value:
            if char.isalpha():
                page_number += char
            else:
                break
        return page_number



class Type(Enumerate):
    options = [
        {'name': 'bool', 'value': u"Boolean", 'type': EnumBoolean},
        {'name': 'dec', 'value': u"Decimal", 'type': NumDecimal},
        {'name': 'digit', 'value': u"00000", 'type': NumDigit},
        {'name': 'hh:mm', 'value': u"HH:MM", 'type': NumShortTime},
        {'name': 'hhh:mm', 'value': u"HHH:MM", 'type': NumTime},
        {'name': 'int', 'value': u"Integer", 'type': NumInteger},
        {'name': 'jj/mm/aaaa', 'value': u"DD/MM/YYYY", 'type': NumDate},
        {'name': 'mm/aaaa', 'value': u"MM/YYYY", 'type': NumShortDate},
        {'name': 'str', 'value': u"String", 'type': UnicodeSQL},
        {'name': 'text', 'value': u"Text", 'type': Text},
        {'name': 'enum', 'value': u"List of values", 'type': SqlEnumerate},
        {'name': 'file', 'value': u"File or Image", 'type': FileImage},
        {'name': 'email', 'value': u"Email", 'type': EmailField}]


    def decode(cls, data):
        data = data.strip().lower()
        if not data:
            # Turn it into default value at the time of writing
            return None
        return Enumerate.decode(data)


    def get_type(cls, name):
        for option in cls.options:
            if option['name'] == name:
                return option['type']
        return None



class ValidInteger(Integer):

    def decode(cls, data):
        data = data.strip()
        if not data:
            # Turn it into default value at the time of writing
            return None
        try:
            value = Integer.decode(data)
        except ValueError:
            value = data
        return value


    def is_valid(cls, value):
        return type(value) is int



class EnumerateOptions(Unicode):
    default = None
    multiple = True


    def decode(cls, data):
        value = Unicode.decode(data)
        return {
            #'name': checkid(value) or '',
            'name': value,
            'value': value}


    def encode(cls, value):
        if value is None:
            return None
        return Unicode.encode(value['value'])


    def is_valid(cls, value):
        return value is not None or value['name'] is not None


    def split(cls, value):
        for separator in (u"\r\n", u"\n"):
            options = value.split(separator)
            if len(options) > 1:
                break
        else:
            # Backwards compatibility
            options = [option.strip() for option in value.split(u"/")]
        return [{
            #'name': checkid(option) or '',
            'name': option,
            'value': option}
                for option in options]



class EnumerateRepresentation(Enumerate):
    options = [
        {'name': 'select', 'value': MSG(u"Select")},
        {'name': 'radio', 'value': MSG(u"Radio")},
        {'name': 'checkbox', 'value': MSG(u"Checkbox")}]


    def decode(cls, data):
        data = data.strip().lower()
        if not data:
            # Turn it into default value at the time of writing
            return None
        return Enumerate.decode(data)



class Mandatory(Boolean):

    def decode(cls, data):
        data = data.strip().upper()
        if not data:
            # Turn it into default value at the time of writing
            return None
        elif data in ('O', 'OUI', 'Y', 'YES', '1'):
            return True
        elif data in ('N', 'NON', 'N', 'NO', '0'):
            return False
        return data


    def is_valid(cls, value):
        return type(value) is bool



class Expression(Unicode):

    def decode(cls, data):
        # Neither upper() nor lower() to preserve enumerates
        value = Unicode.decode(data.strip())
        # Allow single "=" as equals
        value = single_eq.sub(ur"==", value)
        value = (value
                # Alternative to name variables
                .replace(u'#', u'')
                # Non-break spaces
                .replace(u'\u00a0', u'')
                # Fucking replacement
                .replace(u'«', u'"').replace(u'»', u'"'))
        return value


    def is_simple(cls, value):
        if '=' in value or 'in' in value:
            return False
        return True


    def is_valid(cls, value, locals_):
        globals_ = {'SI': SI}
        try:
            eval(value, globals_, locals_)
        except ZeroDivisionError:
            pass
        except Exception:
            # Let error raise with message
            raise
        return True



class SchemaHandler(TableFile):
    # Don't store default values here because any value needs to be written
    # down in case the default value changes later.
    record_properties = {
        'title': Unicode(mandatory=True, title=MSG(u"Title")),
        'name': Variable(mandatory=True, title=MSG(u"Variable")),
        'type': Type(mandatory=True, title=MSG(u"Type")),
        'help': Unicode(title=MSG(u"Online Help")),
        'length': ValidInteger(title=MSG(u"Length")),
        'enum_options': EnumerateOptions(mandatory=True,
            title=MSG(u"Enumerate Options")),
        'enum_repr': EnumerateRepresentation(
            title=MSG(u"Enumerate Representation")),
        'decimals': ValidInteger(title=MSG(u"Decimals")),
        'mandatory': Mandatory(title=MSG(u"Mandatory")),
        'size': ValidInteger(title=MSG(u"Input Size")),
        'dependency': Expression(title=MSG(u"Dependent Field")),
        'formula': Expression(title=MSG(u"Formula")),
        'default': String(default='', title=MSG(u"Default Value"))}
    _schema_pages = None, None


    def get_type(self, name):
        return self.record_properties['type'].get_type(name)


    def _get_schema_pages(self):
        schema = {}
        pages = {}
        get_record_value = self.get_record_value
        for record in self.get_records():
            # The name
            name = get_record_value(record, 'name')
            # The datatype
            type_name = get_record_value(record, 'type')
            datatype = self.get_type(type_name)
            multiple = False
            # TypeError: issubclass() arg 1 must be a class
            if isinstance(datatype, Numeric):
                pass
            elif issubclass(datatype, SqlEnumerate):
                enum_options = get_record_value(record, 'enum_options')
                representation = get_record_value(record, 'enum_repr')
                multiple = (representation == 'checkbox')
                datatype = datatype(options=enum_options,
                        representation=representation)
            elif issubclass(datatype, EnumBoolean):
                datatype = datatype(representation='radio')
                multiple = False
            # The page number (now automatic)
            page_number = Variable.get_page_number(name)
            pages.setdefault(page_number, set()).add(name)
            page_numbers = (page_number,)
            # Add to the datatype
            default = get_record_value(record, 'default')
            if multiple:
                default = [default]
            length = get_record_value(record, 'length')
            size = get_record_value(record, 'size') or length
            schema[name] = datatype(multiple=multiple,
                type=type_name,
                default=datatype.decode(default),
                # Read only for Scrib
                readonly=False,
                pages=page_numbers,
                title=get_record_value(record, 'title'),
                help=get_record_value(record, 'help'),
                length=length,
                decimals=get_record_value(record, 'decimals'),
                mandatory=get_record_value(record, 'mandatory'),
                size=size,
                dependency=get_record_value(record, 'dependency'),
                formula=get_record_value(record, 'formula'))
        return schema, pages


    def get_schema_pages(self):
        """Keep the result in memory. The resource is deleted when new
        parameters are uploaded anyway.
        """
        schema, pages = self._schema_pages
        if schema is None:
            schema, pages = self._schema_pages = self._get_schema_pages()
        return schema, pages



class Schema(Table):
    class_id = 'Schema'
    class_version = '20090123'
    class_title = MSG(u"Schema")
    class_handler = SchemaHandler
    class_icon16 = 'icons/16x16/excel.png'
    class_icon48 = 'icons/48x48/excel.png'

    # To import from CSV
    columns = ['title', 'name', 'type', 'help', 'length', 'enum_options',
            'enum_repr', 'decimals', 'mandatory', 'size', 'dependency',
            'formula', 'default']

    # Views
    view = Table_View(table_actions=freeze([]))
    add_record = None
    edit_record = None
    edit = None


    def _load_from_csv(self, body, skip_header=True):
        handler = self.handler
        # Consistency check
        # First round on variables
        # Starting from 1 + header
        lineno = 2
        locals_ = {}
        for line in parse(body, self.columns, handler.record_properties,
                skip_header=skip_header):
            record = {}
            for index, key in enumerate(self.columns):
                record[key] = line[index]
            # Name
            name = record['name']
            if name is None:
                continue
            if not Variable.is_valid(name):
                raise FormatError, ERR_BAD_NAME(line=lineno, name=name)
            if name in locals_:
                raise FormatError, ERR_DUPLICATE_NAME(line=lineno,
                        name=name)
            # Type
            type_name = record['type']
            if type_name is None:
                # Write down default at this time
                record['type'] = type_name = 'str'
            datatype = handler.get_type(type_name)
            if datatype is None:
                raise FormatError, ERR_BAD_TYPE(line=lineno, type=type_name)
            # Length
            length = record['length']
            if length is None:
                # Write down default at this time
                record['length'] = length = 20
            if not ValidInteger.is_valid(length):
                raise FormatError, ERR_BAD_LENGTH(line=lineno, length=length)
            if issubclass(datatype, SqlEnumerate):
                # Enumerate Options
                enum_option = record['enum_options']
                if enum_option is None:
                    raise FormatError, ERR_MISSING_OPTIONS(line=lineno)
                # Split on "/"
                enum_options = EnumerateOptions.split(enum_option['value'])
                record['enum_options'] = enum_options
                # Enumerate Representation
                enum_repr = record['enum_repr']
                if enum_repr is None:
                    # Write down default at the time of writing
                    record['enum_repr'] = enum_repr = 'radio'
                if not EnumerateRepresentation.is_valid(enum_repr):
                    raise FormatError, ERR_BAD_ENUM_REPR(line=lineno,
                            enum_repr=enum_repr)
            elif issubclass(datatype, NumDecimal):
                # Decimals
                decimals = record['decimals']
                if decimals is None:
                    # Write down default at the time of writing
                    record['decimals'] = decimals = 2
                if not ValidInteger.is_valid(decimals):
                    raise FormatError, ERR_BAD_DECIMALS(line=lineno,
                            decimals=decimals)
            # Mandatory
            mandatory = record['mandatory']
            if mandatory is None:
                # Write down default at the time of writing
                record['mandatory'] = mandatory = True
            if not Mandatory.is_valid(mandatory):
                raise FormatError, ERR_BAD_MANDATORY(line=lineno,
                        mandatory=mandatory)
            # Size
            size = record['size']
            if size is None:
                # Write down default at the time of writing
                if type_name == 'text':
                    record['size'] = size = 5
                else:
                    record['size'] = size = length
            if not ValidInteger.is_valid(size):
                raise FormatError, ERR_BAD_SIZE(line=lineno, size=size)
            # Default value
            default = record['default'] = record['default'].strip()
            if default:
                if issubclass(datatype, EnumBoolean):
                    value = Mandatory.decode(default)
                    default = EnumBoolean.encode(value)
                elif issubclass(datatype, SqlEnumerate):
                    datatype = datatype(options=enum_options)
                    #default = checkid(default) or ''
                    default = default
                elif issubclass(datatype, NumTime):
                    # "0-0-0 09:00:00" -> "09:00:00"
                    default = default.split(' ')[-1]
                    # "09:00:00" -> "09:00"
                    if default.count(":") > 1:
                        default = default.rsplit(":", 1)[0]
                elif issubclass(datatype, NumDate):
                    # "2010-11-18 00:00:00" -> "18/11/2010"
                    default = default.split(' ')[0]
                    value = Date.decode(default)
                    default = NumDate.encode(value)
                elif issubclass(datatype, NumDigit):
                    datatype = datatype(length=length)
                if not datatype.is_valid(default):
                    raise FormatError, ERR_BAD_DEFAULT(line=lineno,
                            default=unicode(default, 'utf_8'))
                record['default'] = default
            handler.add_record(record)
            if record['enum_repr'] == 'checkbox':
                locals_[name] = []
            else:
                locals_[name] = 0
            lineno += 1
        # Second round on references
        # Starting from 1 + header
        lineno = 2
        get_record_value = handler.get_record_value
        for record in handler.get_records():
            dependency = get_record_value(record, 'dependency')
            if dependency:
                try:
                    Expression.is_valid(dependency, locals_)
                except Exception, err:
                    raise FormatError, ERR_BAD_DEPENDENCY(line=lineno,
                            err=err)
            formula = get_record_value(record, 'formula')
            if formula:
                try:
                    datatype.sum
                except AttributeError:
                    raise FormatError, ERR_NO_FORMULA(line=lineno,
                            type=type_name)
                try:
                    Expression.is_valid(formula, locals_)
                except Exception, err:
                    raise FormatError, ERR_BAD_FORMULA(line=lineno, err=err)
            lineno += 1


    def init_resource(self, body=None, filename=None, extension=None,
            skip_header=True, **kw):
        proxy = super(Schema, self)
        proxy.init_resource(filename=filename, extension=extension, **kw)
        self._load_from_csv(body, skip_header=skip_header)


    def get_schema_pages(self):
        return self.handler.get_schema_pages()


    def update_20090123(self):
        handler = self.handler
        for lineno, record in enumerate(handler.get_records()):
            get_record_value = handler.get_record_value
            update_record = handler.update_record
            record_id = record.id
            # representation -> length+enum_repr+decimals
            # Default values at the time of writing
            length = 20
            enum_repr = 'radio'
            decimals = 2
            representation = get_record_value(record, 'representation')[0]
            if "." in representation:
                integer, decimals = representation.split(".")
            elif representation.isdigit():
                length = representation
            elif EnumerateRepresentation.is_valid(representation):
                enum_repr = representation
            update_record(record_id, length=length, enum_repr=enum_repr,
                    decimals=decimals, representation=None)
            # vocabulary -> enum_options
            vocabulary = get_record_value(record, 'vocabulary')[0]
            vocabulary = Unicode.decode(vocabulary)
            enum_options = EnumerateOptions.split(vocabulary)
            handler.update_record(record_id, enum_options=enum_options,
                    vocabulary=None)
