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
from itools.core import merge_dicts
from itools.web import get_context

# Import from ikaaro
from ikaaro.access import is_admin
from ikaaro.skins import Skin as BaseSkin

# Import from goodforms
from form import Form
from utils import is_print



class Skin(BaseSkin):

    def get_template(self):
        if is_print(get_context()):
            return self.get_resource('/ui/goodforms/print.xhtml')
        return super(Skin, self).get_template()


    def get_styles(self, context):
        styles = super(Skin, self).get_styles(context)
        # Restore Aruni
        if '/ui/aruni/style.css' not in styles:
            styles.insert(1, '/ui/aruni/style.css')
        styles.insert(-2,
                '/ui/goodforms/fancybox/jquery.fancybox-1.3.1.css')
        site_root = context.resource.get_site_root()
        # Add specific style on root
        if site_root is context.root:
            wg_style = '%s/root/style.css' % self.get_canonical_path()
            styles.insert(-1, wg_style)
        # Replace root style by website style
        if styles[-1] == '/theme/style/;download':
            if site_root != context.root:
                style = site_root.get_resource('theme/style')
                ac = style.get_access_control()
                if ac.is_allowed_to_view(context.user, style):
                    del styles[-1]
                    styles.append('{0}/;download'.format(
                        context.get_link(style)))

        if isinstance(context.resource, Form) and context.view_name == 'print':
            # Disable custom CSS on print view
            if styles[-1].endswith('/style/;download'):
                del styles[-1]

        return styles


    def get_scripts(self, context):
        scripts = super(Skin, self).get_scripts(context)
        scripts.append('/ui/goodforms/zeroclipboard/ZeroClipboard.js')
        scripts.append(
                '/ui/goodforms/fancybox/jquery.fancybox-1.3.1.pack.js')
        return scripts


    def build_namespace(self, context):
        resource = context.resource
        site_root = resource.get_site_root()
        website_title = site_root.get_title()
        website_href = context.get_link(site_root)
        user = context.user
        theme = site_root.get_resource('theme')
        logo_href = None
        logo_path = theme.get_property('logo')
        if logo_path:
            logo = theme.get_resource(logo_path, soft=True)
            if logo:
                ac = logo.get_access_control()
                if ac.is_allowed_to_view(user, logo):
                    # XXX restore max height behaviour
                    logo_href = '{0}/;thumb?width=475&height=70'.format(
                            context.get_link(logo))
        new_resource_allowed = is_admin(user, resource)
        namespace = merge_dicts(BaseSkin.build_namespace(self, context),
            website_title=website_title, website_href=website_href,
            logo_href=logo_href,
            new_resource_allowed=new_resource_allowed)
        # Hide as much as possible to form user
        if user is not None:
            role = site_root.get_user_role(user.name)
            if role == 'guests':
                #namespace['location'] = None
                namespace['languages'] = None
                #namespace['menu']['items'] = None

        # Home page ?
        page_css = None
        if type(context.resource) == type(context.root):
            if context.view_name in (None, 'view'):
                page_css = 'home-page'
        namespace['page_css'] = page_css

        # Is Admin
        namespace['is_admin'] = is_admin(user, resource)

        return namespace
