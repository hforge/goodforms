# -*- coding: UTF-8 -*-
# Copyright (C) 2006 Luis Belmar Letelier <luis@itaapy.com>
# Copyright (C) 2006, 2008-2010 Hervé Cauwelier <herve@itaapy.com>
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

# Import from the Standard Library
from datetime import date
from decimal import Decimal as dec, InvalidOperation

# Import from itools
from itools.core import merge_dicts, thingy
from itools.datatypes import DataType, Unicode, Enumerate, Email
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.datatypes import FileDataType


def quote_string(data):
    # FIXME removed u"\\" because message extraction crashes
    data = '"{0}"'.format(data.replace('"', '\\"').replace("'", "\\'"))
    return unicode(data, 'utf8')



class DateLitterale(DataType):
    weekdays = ['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi',
                'dimanche']
    # begin at index 1
    months = ['', 'janvier', 'février', 'mars', 'avril', 'mai', 'juin',
              'juillet', 'août', 'septembre', 'octobre', 'novembre',
              'décembre']


    def encode(cls, value):
        if not value:
            return ''
        return (value.strftime("# %d & %Y")
                     .replace('#', cls.weekdays[value.weekday()])
                     .replace('&', cls.months[value.month]))



# The reason these datatypes are instances and not thingies is that I need to
# call "+", "int", etc. for the formulas and controls

class Numeric(thingy):
    """All arithmetical operations."""
    default = ''


    ########################################################################
    # DataType API
    @classmethod
    def get_default(cls):
        return cls.decode(cls.default)


    @classmethod
    def is_valid(cls, data):
        # 0009003: les séparateurs de millers provoquent une erreur
        data = ''.join(data.split())
        try:
            cls(data)
        except Exception:
            return False
        return True


    @classmethod
    def decode(cls, data):
        if isinstance(data, Numeric):
            return data
        elif data is None or str(data).upper() == 'NC':
            return cls('NC')
        elif type(data) is str:
            # 0009003: les séparateurs de millers provoquent une erreur
            data = ''.join(data.split())
        return cls(data)


    @classmethod
    def encode(cls, value):
        if isinstance(value, cls):
            value = value.value
        if value is None:
            return 'NC'
        return str(value)


    @classmethod
    def encode_sql(cls, value):
        if isinstance(value, cls):
            if value.value is None or value.value == '':
                return u"null"
        return quote_string(cls.encode(value))


    def __call__(self, **kw):
        kw = merge_dicts(vars(self), kw)
        return self.__class__(**kw)


    ########################################################################
    # Numeric API
    def __init__(self, **kw):
        object.__init__(self)
        for key, value in kw.iteritems():
            setattr(self, key, value)


    def __str__(self):
        return self.encode(self.value)


    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, vars(self))


    def __int__(self):
        if self.value is None:
            raise NotImplemented
        return int(self.value)


    def __float__(self):
        if self.value is None:
            raise NotImplemented
        return float(self.value)


    def __add__(self, right):
        left = self.value
        if left is None:
            # NC + right = NC
            return self.__class__('NC')
        if isinstance(right, Numeric):
            right = right.value
            if right is None:
                # left + NC = NC
                return self.__class__('NC')
        if left == '':
            left = 0
        left = dec(str(left))
        if right == '':
            right = 0
        right = dec(str(right))
        # <type> + <type>
        return self.__class__(left + right)

    __radd__ = __add__


    def __sub__(self, right):
        left = self.value
        if left is None:
            # NC - right = NC
            return self.__class__('NC')
        if isinstance(right, Numeric):
            right = right.value
            if right is None:
                # left - NC = NC
                return self.__class__('NC')
        if left == '':
            left = 0
        left = dec(str(left))
        if right == '':
            right = 0
        right = dec(str(right))
        # <type> - <type>
        return self.__class__(left - right)


    def __rsub__(self, left):
        right = self.value
        if right is None:
            # left - NC = NC
            return self.__class__('NC')
        if isinstance(left, Numeric):
            left = left.value
            if left is None:
                # NC - right = NC
                return self.__class__('NC')
        if left == '':
            left = 0
        left = dec(str(left))
        if right == '':
            right = 0
        right = dec(str(right))
        # <type> - <type>
        return self.__class__(left - right)


    def __mul__(self, right):
        left = self.value
        if left is None:
            # NC * right = NC
            return self.__class__('NC')
        if isinstance(right, Numeric):
            right = right.value
            if right is None:
                # left * NC = NC
                return self.__class__('NC')
        if left == '':
            left = 0
        left = dec(str(left))
        if right == '':
            right = 0
        right = dec(str(right))
        # <type> * <type>
        return self.__class__(left * right)

    __rmul__ = __mul__


    def __div__(self, right):
        left = self.value
        if left is None:
            # NC / right = NC
            return self.__class__('NC')
        if isinstance(right, Numeric):
            right = right.value
            if right is None:
                # left / NC = NC
                return self.__class__('NC')
        if left == '':
            left = 0
        if left == 0:
            # Pas de division par zéro !
            return self.__class__(0)
        left = dec(str(left))
        if right == '':
            right = 0
        if right == 0:
            # Pas de division par zéro !
            return self.__class__(0)
        right = dec(str(right))
        # <type> / <type>
        return self.__class__(left / right)


    def __rdiv__(self, left):
        right = self.value
        if right is None:
            # left / NC = NC
            return self.__class__('NC')
        if isinstance(left, Numeric):
            left = left.value
            if left is None:
                # NC / right = NC
                return self.__class__('NC')
        if left == '':
            left = 0
        if left == 0:
            # Pas de division par zéro !
            return self.__class__(0)
        left = dec(str(left))
        if right == '':
            right = 0
        if right == 0:
            # Pas de division par zéro !
            return self.__class__(0)
        right = dec(str(right))
        # <type> / <type>
        return self.__class__(left / right)


    def __gt__(self, right):
        left = self.value
        if isinstance(right, Numeric):
            right = right.value
        if right is 'NC' or right is None:
            # left > NC
            return True
        elif left is None:
            # NC > right
            return True
        # <type> > <type>
        return left > right


    def __ge__(self, right):
        left = self.value
        if isinstance(right, Numeric):
            right = right.value
        if right is 'NC' or right is None:
            # left >= NC
            return True
        elif left is None:
            # NC >= right
            return True
        # <type> >= <type>
        return left >= right


    def __lt__(self, right):
        left = self.value
        if isinstance(right, Numeric):
            right = right.value
        if right is 'NC' or right is None:
            # left < NC
            return True
        elif left is None:
            # NC < right
            return True
        # <type> < <type>
        return left < right


    def __le__(self, right):
        left = self.value
        if isinstance(right, Numeric):
            right = right.value
        if right is 'NC' or right is None:
            # left <= NC
            return True
        elif left is None:
            # NC <= right
            return True
        # <type> <= <type>
        return left <= right


    def __eq__(self, right):
        left = self.value
        if isinstance(right, Numeric):
            right = right.value
        if left is None:
            # NC == right
            return True
        elif str(right).upper() == 'NC' or right is None:
            # <type> == NC
            return True
        # <type> == <type>
        return left == right


    def __ne__(self, right):
        left = self.value
        if isinstance(right, Numeric):
            right = right.value
        if left is None:
            # NC != right
            return str(right).upper() != 'NC' and right is not None
        elif str(right).upper() == 'NC' or right is None:
            # <type> != NC
            return True
        # <type> != <type>
        return left != right


    def __cmp__(self, right):
        # Toutes les combinaisons ont été épuisées
        raise NotImplemented


    def __bool__(self):
        # FIXME seulement dans Python 3 ?
        raise NotImplemented


    def __nonzero__(self):
        return bool(self.value)


    def __len__(self):
        raise NotImplemented


    @staticmethod
    def clean(data):
        # 0009003: les séparateurs de millers provoquent une erreur
        data = ''.join(data.split())
        if "," in data and "." in data:
            if data.index(",") < data.index("."):
                # en
                data = data.replace(",", "")
            else:
                # fr
                data = data.replace(".", "")
        return data.replace(" ", "").replace(",", ".")


    @classmethod
    def sum(cls, formula, schema, fields):
        sum = cls.decode(0)
        for term in formula.split('+'):
            term = term.strip()
            data = fields.get(term)
            if not data:
                try:
                    data = schema[term].default
                except:
                    return None
            if not data:
                return None
            if str(data).upper() == 'NC':
                return 'NC'
            datatype = schema[term]
            try:
                value = datatype.decode(data)
            except Exception:
                return None
            if not datatype.is_valid(datatype.encode(value)):
                return None
            sum += value
        return sum



class NumDecimal(Numeric):

    def __init__(self, value=None, **kw):
        super(NumDecimal, self).__init__(**kw)
        if value is not None:
            if str(value).upper() == 'NC':
                value = None
            elif type(value) is dec or value == '':
                pass
            else:
                test = value
                if type(value) is str:
                    test = self.clean(value)
                else:
                    test = str(value)
                try:
                    value = dec(test)
                except InvalidOperation:
                    pass
        self.value = value


    def round(self, digits=2):
        value = self.value
        if value is None or type(value) is str:
            return value
        places = dec('10') ** -digits
        return value.quantize(places)


    @staticmethod
    def decode(value):
        if value == '':
            return None
        return int(value)


    @staticmethod
    def encode(value):
        if value is None:
            return ''
        return str(value).replace(' ', '').replace(',','.')


    @classmethod
    def get_default(cls):
        return cls.default


    @classmethod
    def is_valid(cls, data):
        if data.upper() == 'NC':
            return True
        try:
            dec(cls.clean(data))
        except InvalidOperation:
            return False
        return True


    def get_sql_schema(self):
        return "decimal({0.length}.{0.decimals}) default 0.0".format(self)



class NumInteger(Numeric):

    def __init__(self, value=None, **kw):
        super(NumInteger, self).__init__(**kw)
        if value is not None:
            if str(value).upper() == 'NC':
                value = None
            elif type(value) is int or value == '':
                pass
            else:
                test = value
                if type(value) is str:
                    test = self.clean(value)
                else:
                    test = str(value)
                try:
                    value = int(float(test))
                except ValueError:
                    pass
        self.value = value


    @staticmethod
    def decode(value):
        if value == '':
            return None
        return int(value)


    @staticmethod
    def encode(value):
        if value is None:
            return ''
        return str(value)


    @classmethod
    def get_default(cls):
        return cls.default

    @classmethod
    def is_valid(cls, data):
        if data.upper() == 'NC':
            return True
        try:
            int(float(cls.clean(data)))
        except ValueError:
            return False
        return True


    def get_sql_schema(self):
        return "int({0}.length) default 0".format(self)



class NumTime(Numeric):

    def __init__(self, value=None, **kw):
        super(NumTime, self).__init__(**kw)
        if value is not None:
            if str(value).upper() == 'NC':
                value = None
            elif type(value) is int or value == '':
                pass
            elif type(value) is str:
                value = value.replace('h', ':')
                if ':' in value:
                    hours, minutes = value.split(':')
                    value = int(hours) * 60 + int(minutes)
            else:
                value = int(value)
        self.value = value


    @classmethod
    def encode(cls, value):
        if isinstance(value, cls):
            value = value.value
        if value is None:
            return 'NC'
        elif type(value) is str:
            return value
        return '%03d:%02d' % (value / 60, value % 60)


    @staticmethod
    def is_valid(data):
        if data == '' or data.upper() == 'NC':
            return True
        data = data.replace('h', ':')
        if data.count(':') != 1:
            return False
        for x in data.split(':'):
            try:
                int(x)
            except ValueError:
                return False
        return True


    def get_sql_schema(self):
        return "char(6) default '000:00'"



class NumShortTime(NumTime):

    @classmethod
    def encode(cls, value):
        if isinstance(value, cls):
            value = value.value
        if value is None:
            return 'NC'
        elif type(value) is str:
            return value
        return '%02d:%02d' % (value / 60, value % 60)


    def get_sql_schema(self):
        return "char(5) default '00:00'"



class NumDate(Numeric):

    def __init__(self, value=None, **kw):
        super(NumDate, self).__init__(**kw)
        if value is not None:
            if type(value) == type(self):
                value = value.value
            if str(value).upper() == 'NC':
                value = None
            elif type(value) is date:
                pass
            elif value == '':
                pass
            else:
                parts = value.split('/')
                if len(parts) == 1:
                    parts = []
                    while len(parts) != 3:
                        parts.insert(0, 1)
                if len(parts) == 2:
                    # Support ShortDate
                    parts.insert(0, 1)
                d, m, y = [int(x) for x in parts]
                # 2-digit year
                if y < 10:
                    y += 2000
                elif y < 100:
                    y += 1900
                value = date(y, m, d)
        self.value = value


    @classmethod
    def encode(cls, value):
        if isinstance(value, cls):
            value = value.value
        if value is None:
            return ''
        if not isinstance(value, date) and not isinstance(value, str):
            value = value.value
        if type(value) is str:
            return value
        return value.strftime('%d/%m/%Y')


    @staticmethod
    def decode(value):
        if value == '':
            return ''
        return value


    @classmethod
    def get_default(cls):
        return cls.default


    @staticmethod
    def is_valid(data):
        if data.upper() == 'NC':
            return True
        if data.count('/') not in (1, 2):
            return False
        try:
            parts = [int(x) for x in data.split('/')]
        except ValueError:
            return False
        # NumShortDate
        if len(parts) == 2:
            parts.insert(0, 1)
        d, m, y = parts
        try:
            date(y, m, d)
        except ValueError:
            return False
        return True


    def get_sql_schema(self):
        return "char(10) default null"




class NumShortDate(NumDate):

    @classmethod
    def encode(cls, value):
        data = super(NumShortDate, cls).encode(value)
        if data == '' or data == 'NC':
            return data
        return data[3:]


    def get_sql_schema(self):
        return "char(7) default null"



class NumDigit(Numeric):

    def __init__(self, value=None, **kw):
        super(NumDigit, self).__init__(**kw)
        if value is not None:
            if str(value).upper() == 'NC':
                value = None
            else:
                pass
        self.value = value


    # XXX not a classmethod
    def is_valid(self, data):
        return data.isdigit() if len(data) == self.length else data == ''


    def get_sql_schema(self):
        return "char({0}.length) default null".format(self)



class UnicodeSQL(Unicode):
    default = ''


    def is_valid(cls, data):
        try:
            unicode(data, 'utf8')
        except Exception:
            return False
        return True


    def get_sql_schema(cls):
        return "varchar({0}.length) default null".format(cls)


    def encode_sql(cls, value):
        if value is None:
            return u"null"
        return quote_string(cls.encode(value))

    @classmethod
    def sum(cls, formula, schema, fields):
        sum = ""
        for term in formula.split('+'):
            term = term.strip()
            data = fields.get(term)
            if not data:
                data = schema[term].default
            if type(data) == type(""):
                data = data.decode("utf-8")
            sum += data
        return sum



class Text(UnicodeSQL):

    def decode(cls, data, encoding='UTF-8'):
        value = super(Text, cls).decode(data, encoding=encoding)
        # Restaure les retours chariot
        return value.replace(u'\\r\\n', u'\r\n')


    def encode(cls, value, encoding='UTF-8'):
        # Stocke tout sur une ligne
        value = value.replace(u'\r\n', u'\\r\\n')
        return super(Text, cls).encode(value, encoding=encoding)

    @classmethod
    def sum(cls, formula, schema, fields):
        sum = cls.decode("")
        for term in formula.split('+'):
            term = term.strip()
            data = fields.get(term)
            if not data:
                return None
            if str(data).upper() == 'NC':
                return 'NC'
            datatype = schema[term]
            try:
                value = datatype.decode(data)
            except Exception:
                return None
            if not datatype.is_valid(datatype.encode(value)):
                return None
            sum += value
        return sum


class EnumBoolean(Enumerate):
    default = ''
    options = [
        {'name': '1', 'value': MSG(u"Yes")},
        {'name': '2', 'value': MSG(u"No")},
    ]


    def decode(cls, data):
        if data == '1':
            return True
        elif data == '2':
            return False
        return data


    def encode(cls, value):
        if value is True:
            return '1'
        elif value is False:
            return '2'
        return value


    def get_sql_schema(cls):
        return "tinyint default null"


    def encode_sql(cls, value):
        if value is None or value == '':
            return u"null"
        return quote_string(cls.encode(value))



class SqlEnumerate(Enumerate):
    default = ''


    def get_sql_schema(cls):
        return "varchar(20) default null"


    def encode_sql(cls, value):
        if value is None or value == '':
            return u"null"
        return quote_string(cls.encode(value))


    def get_values(cls, value):
        return (cls.get_value(value, value) for value in value)



class Subscription(Enumerate):
    options = [
        {'name': 'restricted',
            'value': MSG(u"Restricted (users must be subscribed)")},
        {'name': 'open',
            'value': MSG(u"Open (accounts are created on demand)")},
        {'name': 'demo',
            'value': MSG(u"Demo (public demo)")}]



class FileImage(FileDataType):

    def encode(cls, value):
        return value


    def decode(cls, data):
        """Find out the resource class (the mimetype sent by the browser can
        be minimalistic).
        """
        if type(data) is str:
            return data
        return super(FileImage, cls).decode(data)



class EmailField(Email):
    def is_valid(cls, value):
        return Email.is_valid(value)
