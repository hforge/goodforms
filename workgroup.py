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
from ikaaro.fields import Char_Field, Boolean_Field
from ikaaro.folder import Folder

# Import from goodforms
from application import Application
from base_views import FrontView
from workgroup_views import Workgroup_NewInstance, Workgroup_View
from workgroup_views import Workgroup_Edit


class Workgroup(Folder):

    class_id = 'Workgroup'
    class_title = MSG(u"GoodForms Workgroup")
    class_description = MSG(u"Create your client space to manage collection applications and submit them.")
    class_views = ['view', 'edit', 'show', 'new_resource']

    # Fields
    logo = Char_Field
    accept_terms_of_use = Boolean_Field

    def get_document_types(self):
        return [Application]

    def get_logo_icon(self, size=48):
        return None

    # Views
    new_instance = Workgroup_NewInstance()
    view = Workgroup_View()
    edit = Workgroup_Edit()
    show = FrontView(title=MSG(u"Your Collection Applications"))
