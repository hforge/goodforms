# -*- coding: UTF-8 -*-
# Copyright (C) 2006, 2008-2010 Hervé Cauwelier <herve@itaapy.com>
# Copyright (C) 2009 Taverne Sylvain <sylvain@itaapy.com>
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
from itools.web import STLView

# Import from ikaaro
from ikaaro.buttons import Remove_BrowseButton

# Import from agitools
from agitools.autotable import AutoTable


class Root_ViewAdmin(STLView):

    access = 'is_admin'
    title = MSG(u'Administration')
    template = "/ui/goodforms/root/admin_view.xml"



class Root_ShowAllWorkgroups(AutoTable):

    access = 'is_admin'
    title = MSG(u'All worlgroups')

    base_classes = ('Workgroup',)
    search_fields = []
    table_fields = ['checkbox', 'logo', 'name', 'title', 'members', 'vhosts']
    table_actions = [Remove_BrowseButton]

    def get_item_value(self, resource, context, item, column):
        if column == 'vhosts':
            return '\n'.join(item.get_value(column))
        elif column == 'logo':
            return None
        elif column == 'members':
            members = [context.root.get_user(x).get_title()
                for x in item.get_value('members')]
            return u', '.join(members)
        # Ok
        proxy = super(Root_ShowAllWorkgroups, self)
        return proxy.get_item_value(resource, context, item, column)



class Root_ShowAllApplications(AutoTable):

    access = 'is_admin'
    base_classes = ('Application',)
    search_fields = []
    title = MSG(u'All applications')
    table_fields = ['checkbox', 'title', 'max_users']
    table_actions = [Remove_BrowseButton]

    def get_item_value(self, resource, context, item, column):
        if column == 'title':
            workgroup = item.parent
            title = u"%s » %s" % (workgroup.get_title(), item.get_title())
            return title, context.get_link(item)
        elif column == 'max_users':
            subscribed = len(list(item.get_forms()))
            max_users = item.get_value('max_users')
            return u"%s/%s" % (subscribed, max_users)
        # Ok
        proxy = super(Root_ShowAllApplications, self)
        return proxy.get_item_value(resource, context, item, column)
