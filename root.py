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

# Import from goodforms
from base_views import  LoginView
from root_views import Root_View, Root_Show
from root_views import Root_ViewAdmin
from root_views import Root_ShowAllWorkgroups, Root_ShowAllApplications
from workgroup import Workgroup


class Root(BaseRoot):

    class_id = 'goodforms'
    class_skin = 'goodforms'
    class_title = MSG(u'Goodforms')
    class_views = ['view', 'view_admin', 'edit', 'show', 'show_all_workgroups', 'show_all_applications']

    def get_user_role(self, name):
        return u'XXX'


    def get_document_types(self):
        return [Workgroup]


    def get_page_title(self):
        return None


    def is_authenticated(self, user, resource):
        return user is not None


    # Views
    view = Root_View()
    view_admin = Root_ViewAdmin()
    _fields = ['title']
    edit = AutoEdit(fields=_fields)
    show = Root_Show()
    show_all_workgroups = Root_ShowAllWorkgroups()
    show_all_applications = Root_ShowAllApplications()

    # Security
    login = LoginView()
    unauthorized = LoginView()
