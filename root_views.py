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
from itools.core import merge_dicts,freeze
from itools.datatypes import Unicode, Email, XMLContent
from itools.gettext import MSG
from itools.uri import encode_query, get_reference, Reference
from itools.web import STLView
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro.autoform import AutoForm
from ikaaro.widgets import TextWidget
from ikaaro.buttons import Remove_BrowseButton

# Import from agitools
from agitools.autotable import AutoTable

# Import from goodforms
from application import Application
from base_views import FrontView
from buttons import CreateButton
from workgroup import Workgroup


class Root_ViewAdmin(STLView):

    access = 'is_admin'
    template = "/ui/goodforms/root/admin_view.xml"


class Root_View(AutoForm):
    access = True
    title = MSG(u"View")
    template = "/ui/goodforms/root/view.xml"

    actions = freeze([CreateButton])
    schema = freeze({
        'title': Unicode(mandatory=True)})
    widgets = freeze([
        TextWidget('title', title=MSG(u'Name of your client space'),
            tip=MSG(u'You can type the name of your company or '
                    u'organization'))])

    anonymous_schema = freeze({
        'email': Email(mandatory=True)})
    anonymous_widgets = freeze([
        TextWidget('email', title=MSG(u"E-mail Address"))])

    scripts = ['/ui/goodforms/js/jquery.jcarousel.min.js']


    def get_schema(self, resource, context):
        schema = self.schema
        if context.user is None:
            schema = freeze(merge_dicts(schema, self.anonymous_schema))
        return schema


    def get_widgets(self, resource, context):
        widgets = self.widgets
        if context.user is None:
            widgets = widgets + self.anonymous_widgets
        return widgets


    def get_namespace(self, resource, context):
        proxy = super(Root_View, self)
        namespace = proxy.get_namespace(resource, context)

        # widgets
        namespace['widgets_dict'] = {}

        # extra anonymous requirements
        user = context.user
        anonymous = user is None
        namespace['anonymous'] = anonymous

        # css
        box_type = None
        if not anonymous:
            workgroups = []
            for child in resource.search_resources(cls=Workgroup):
                root = resource.get_resource('/')
                if not root.is_allowed_to_view(user, child):
                    continue

            workgroups_len = len(workgroups)
            if not workgroups_len:
                box_type = 'type3'
            elif workgroups_len == 1:
                box_type = 'type2'
            else:
                box_type = 'type4'

        namespace['box_type'] = box_type

        # Your workgroups link/title
        your_workgroups = None
        if box_type in ('type2', 'type4'):
            if box_type == 'type2':
                title = MSG(u'Your workgroup')
            else:
                title = MSG(u'Your workgroups')
            your_workgroups = {'link': '/;show',
                               'title': title}
        namespace['your_workgroups'] = your_workgroups

        # home page content
        homepage = resource.get_value('homepage')
        if homepage is None:
            # Avoid response abort
            homepage = None
        namespace['homepage_content'] = homepage

        # slogan
        namespace['slogan'] = resource.get_value('slogan')
        # Action
        namespace['action'] = None
        namespace['widgets'] = []
        # Ok
        return namespace


    def action(self, resource, context, form):
        goto = '/;new_resource'
        query = {'type': 'Workgroup'}
        schema = self.get_schema(resource, context)
        for key, datatype in schema.iteritems():
            if key in form:
                query[key] = datatype.encode(form[key])
        return get_reference('%s?%s' % (goto, encode_query(query)))



class Root_Show(FrontView):
    template = '/ui/goodforms/root/show.xml'
    title = MSG(u"Your Client Space")
    cls = Workgroup
    size = 128
    cols = 5


    def get_namespace(self, resource, context):
        proxy = super(Root_Show, self)
        namespace = proxy.get_namespace(resource, context)
        if isinstance(namespace, Reference):
            return namespace

        namespace['size'] = self.size

        members = []
        guests = []
        for item in namespace['items']:
            if item['icon'] is None:
                item['icon'] = None
            if item['role'] == 'members':
                rows = members
            else:
                rows = guests
            if not rows:
                rows.append([])
            rows[-1].append(item)
            if len(rows[-1]) == self.cols:
                rows.append([])
        namespace['members'] = members
        namespace['guests'] = guests
        return namespace





class Root_ShowAllWorkgroups(AutoTable):

    access = 'is_admin'
    search_cls = Workgroup
    search_class_id = 'Workgroup'
    search_fields = []
    table_fields = ['checkbox', 'logo', 'name', 'title', 'members', 'vhosts']
    table_actions = [Remove_BrowseButton]
    batch_size = 0

    def get_item_value(self, resource, context, item, column):
        brain, item_resource = item
        if column == 'vhosts':
            return '\n'.join(item_resource.get_value(column))
        elif column == 'logo':
            icon = item_resource.get_logo_icon()
            icon = XMLContent.encode(icon)
            return XMLParser('<img src="%s"/>' % icon)
        elif column == 'members':
            members = [context.root.get_user(x).get_title()
                for x in item_resource.get_value('members')]
            return u', '.join(members)
        proxy = super(Root_ShowAllWorkgroups, self)
        return proxy.get_item_value(resource, context, item, column)



class Root_ShowAllApplications(AutoTable):

    access = 'is_admin'
    search_cls = Application
    search_class_id = 'Application'
    search_fields = []
    table_fields = ['checkbox', 'title', 'max_users']
    table_actions = [Remove_BrowseButton]
    batch_size = 0

    def get_item_value(self, resource, context, item, column):
        brain, item_resource = item
        if column == 'title':
            workgroup = item_resource.parent
            title = u"%s » %s" % (workgroup.get_title(),
                item_resource.get_title())
            return title, context.get_link(item_resource)
        elif column == 'max_users':
            subscribed = len(list(item_resource.get_forms()))
            max_users = item_resource.get_value('max_users')
            return u"%s/%s" % (subscribed, max_users)
        proxy = super(Root_ShowAllApplications, self)
        return proxy.get_item_value(resource, context, item, column)
