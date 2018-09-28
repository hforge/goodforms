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

# Import from itools
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.autoedit import AutoEdit
from ikaaro.root import Root as BaseRoot

# Import from agitools
from agitools.utils_views import IconsView

# Import from goodforms
from application import Applications
from root_views import Root_ViewAdmin


class Root(BaseRoot):

    class_id = 'goodforms'
    class_skin = 'goodforms'
    class_title = MSG(u'Goodforms')
    class_views = ['view', 'view_admin', 'edit' ]

    def init_resource(self, *args, **kw):
        super(Root, self).init_resource(*args, **kw)
        self.make_resource('applications', Applications)


    def get_user_role(self, name):
        return u'XXX'


    def get_page_title(self):
        return None


    def is_authenticated(self, user, resource):
        return user is not None


    # Views
    view = IconsView
    view_admin = Root_ViewAdmin()
    _fields = ['title']
    edit = AutoEdit(fields=_fields)
