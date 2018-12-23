# -*- coding: UTF-8 -*-
# Copyright (C) 2006 Luis Belmar Letelier <luis@itaapy.com>
# Copyright (C) 2008-2010 Hervé Cauwelier <herve@itaapy.com>
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

# Import from itools
from itools.core import is_prototype
from itools.gettext import MSG
from itools.web import STLView

# Import from goodforms
from datatypes import Numeric, UnicodeSQL


def is_print(context):
    return context.get_query_value('view') == 'print'


def set_print(context):
    context.query['view'] = 'print'



def get_page_number(name):
    try:
        _, page_number = name.split('page')
    except ValueError:
        return None
    return page_number.upper()



def group_by_items(items, max_in_a_row=4):
    if not items:
        return []
    groups = []
    for i in range(0, len(items), max_in_a_row):
        groups.append(items[i:i+max_in_a_row])
    return groups


def SI(condition, iftrue, iffalse=True):
    if condition:
        value = iftrue
    else:
        value = iffalse
    return value



def parse_control(title):
    """Découpe le titre du contrôle pour remplacer les patterns du type ::

        « A123 : mauvaise valeur [A123] »

    par ::

        « A123 : mauvaise valeur [toto] »
    """
    generator = enumerate(title)
    end = 0
    for start, char in generator:
        if char == u'[':
            yield False, title[end:start+1]
            for end, char2 in generator:
                if char2 == u']':
                    yield True, title[start + 1:end]
                    break
    yield False, title[end:]



def force_encode(value, datatype, encoding):
    if datatype.multiple:
        return ' '.join(value)
    try:
        # TypeError: issubclass() arg 1 must be a class
        if isinstance(datatype, Numeric):
            return datatype.encode(value)
        elif issubclass(datatype, UnicodeSQL):
            return datatype.encode(value, encoding)
        return datatype.encode(value)
    except ValueError:
        return unicode(value).encode(encoding)



class FormatError(ValueError):

    def __init__(self, message, *args, **kw):
        if is_prototype(message, MSG):
            message = message.gettext()
        return super(FormatError, self).__init__(message, *args, **kw)



class IconsView(STLView):

    access = 'is_authenticated'
    title = MSG(u'Voir')
    template = '/ui/goodforms/icons_view.xml'
    resources_names = []

    def get_namespace(self, resource, context):
        items = []
        root = context.root
        for r in resource.get_resources():
            if not root.is_allowed_to_view(context.user, r):
                continue
            # Check module access
            kw = {'class_icon_css': getattr(r, 'class_icon_css', 'fa-pencil-alt'),
                  'title': r.class_title,
                  'abspath': str(r.abspath),
                  'link': context.get_link(r)}
            items.append(kw)
        return {'items_by_group': group_by_items(items, 6)}
