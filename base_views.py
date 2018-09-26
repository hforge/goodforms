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

# Import from the Standard Library
from operator import itemgetter

# Import from itools
from itools.core import merge_dicts, freeze
from itools.datatypes import Email, String
from itools.stl import stl
from itools.uri import get_reference, get_uri_path, Reference
from itools.web import INFO, ERROR

# Import from ikaaro
from ikaaro.folder import Folder
from ikaaro.folder_views import Folder_BrowseContent, Folder_PreviewContent
from ikaaro.resource_ import DBResource
from ikaaro.resource_views import DBResource_Links, DBResource_Backlinks
from ikaaro.revisions_views import DBResource_CommitLog
from ikaaro.views import IconsView as BaseIconsView

# Import from goodforms
from datatypes import EmailField


MSG_NO_RESOURCE = ERROR(u'No {class_title} available.')


class FrontView(BaseIconsView):
    access = 'is_authenticated'
    cls = None
    size = 48


    def get_namespace(self, resource, context):
        user = context.user
        items = []
        for child in resource.search_resources(cls=self.cls):
            if not context.root.is_allowed_to_view(user, child):
                continue
            title = child.get_title()
            items.append({'icon': None,
                'title': title,
                'description': child.get_value('description'),
                'url': context.get_link(child),
                'sort': title.lower(),
                # XXX Utilisé par Root_Show
                'role': 'XXX'})
        if not items:
            class_title = self.cls.class_title.gettext()
            return context.come_back(MSG_NO_RESOURCE,
                class_title=class_title)
        elif len(items) == 1:
            return get_reference(items[-1]['url'])
        items.sort(key=itemgetter('sort'))
        return {'batch': None, 'items': items}



# Security
DBResource.links = DBResource_Links(access='is_admin')
DBResource.backlinks = DBResource_Backlinks(access='is_admin')
DBResource.commit_log = DBResource_CommitLog(access='is_admin')
Folder.browse_content = Folder_BrowseContent(access='is_admin')
Folder.preview_content = Folder_PreviewContent(access='is_admin')
