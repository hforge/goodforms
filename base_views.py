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
from ikaaro.resource_views import LoginView as BaseLoginView
from ikaaro.resource_views import LogoutView as BaseLogoutView
from ikaaro.revisions_views import DBResource_CommitLog
from ikaaro.views import IconsView as BaseIconsView

# Import from goodforms
from datatypes import EmailField


MSG_NO_RESOURCE = ERROR(u'No {class_title} available.')



# Pas d'héritage pour pas de méthode "action"
class LoginView(BaseLoginView):
    template = '/ui/goodforms/base/login.xml'
    schema = freeze({
        'username': String,
        'password': String,
        'email': EmailField})


    def action_login(self, resource, context, form):
        email = form['username'].strip()
        password = form['password']

        user = context.root.get_user_from_login(email)
        if user is None or not user.authenticate(password):
            message = u'The e-mail or the password is incorrect.'
            context.message = ERROR(message)
            return

        # Set cookie & context
        context.login(user)

        # Come back
        referrer = context.get_referrer()
        if referrer is None:
            goto = get_reference('./')
        else:
            path = get_uri_path(referrer)
            if path.endswith(';login'):
                goto = get_reference('./')
            else:
                goto = referrer

        # At the root, redirect to the workgroup or application
        if type(goto) is not Reference:
            goto = get_reference(goto)
        if resource.abspath.resolve(goto.path) == '/':
            if not context.root.is_admin(user, resource):
                goto = get_reference('/;show')

        # FIXME avoid redirecting to user home
        print "goto", goto
        return context.come_back(INFO(u"Welcome!"), goto)


    def action_register(self, resource, context, form):
        email = form['email'].strip()
        if not Email.is_valid(email):
            message = u'The given username is not an e-mail address.'
            context.message = ERROR(message)
            return

        user = context.root.get_user_from_login(email)

        # Case 1: Register
        if user is None:
            if context.site_root.is_allowed_to_register():
                return self._register(resource, context, email)
            error = u"You are not allowed to register."
            context.message = ERROR(error)
            return

        # Case 2: Forgotten password
        email = user.get_property('email')
        user.send_forgotten_password(context, email)
        path = '/ui/website/forgotten_password.xml'
        handler = resource.get_resource(path)
        return stl(handler)



class LogoutView(BaseLogoutView):

    def GET(self, resource, context):
        proxy = super(LogoutView, self)
        goto = proxy.GET(resource, context)
        goto.path = goto.path.resolve('/')
        return goto



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
                'description': child.get_property('description'),
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



class IconsView(BaseIconsView):
    template = '/ui/goodforms/base/icons_view.xml'
    item_keys = ('icon', 'title', 'description', 'url', 'description_url',
            'rel', 'onclick', 'access', 'extra')
    cols = 3


    @classmethod
    def make_item(cls, **kw):
        item = {}
        for key in cls.item_keys:
            if key in kw:
                item[key] = kw[key]
            else:
                item[key] = None
        return item


    def get_items(self, resource, context):
        return [x.copy() for x in self.items]


    @staticmethod
    def resolve_path(item, key, base_path):
        value = item[key]
        if value is None:
            return
        path = item[key] = str(base_path.resolve2(value))
        return path


    def get_namespace(self, resource, context):
        namespace = {}
        namespace['batch'] = None
        namespace['width'] = 100 // self.cols

        here_path = context.uri.path
        name = here_path.get_name()
        if name and not name[0] == ';':
            view = context.resource.get_default_view_name()
            here_path = here_path.resolve2(';' + view)

        base_path = resource.abspath

        rows = [[]]
        for item in self.get_items(resource, context):
            path = self.resolve_path(item, 'url', base_path)
            self.resolve_path(item, 'description_url', base_path)
            # Fragment not sent
            if path.split('#', 1)[0] == here_path:
                item['class'] = 'active'
            else:
                item['class'] = None
            method_name = item['access']
            if method_name:
                method = getattr(self, method_name)
                item = item.copy()
                if not method(item, resource, context):
                    item['url'] = None
                    item['onclick'] = None
                    item['icon'] = item['icon'].replace('.png', '-grey.png')
            rows[-1].append(item)
            if len(rows[-1]) == self.cols:
                rows.append([])
        namespace['rows'] = rows

        return namespace



DBResource.login = LoginView()
DBResource.logout = LogoutView()
# Security
DBResource.links = DBResource_Links(access='is_admin')
DBResource.backlinks = DBResource_Backlinks(access='is_admin')
DBResource.commit_log = DBResource_CommitLog(access='is_admin')
Folder.browse_content = Folder_BrowseContent(access='is_admin')
Folder.preview_content = Folder_PreviewContent(access='is_admin')
