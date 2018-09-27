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
from itools.web import INFO, ERROR

# Import from ikaaro
from ikaaro.autoadd import AutoAdd
from ikaaro.autoedit import AutoEdit
from ikaaro import messages

# Import from agitiols
from agitools.autotable import AutoTable
from agitools.fields import Fake_Field


MSG_NEW_WORKGROUP = INFO(u'Your client space is created. You can add your logo.')
MSG_ERR_NOT_IMAGE = ERROR(u'Not an image or invalid image.')
MSG_BAD_PASSWORD = ERROR(u'You already have an account but your password did not match. Try <a href="/;login">log in</a> first.', format='html')


class Workgroup_NewInstance(AutoAdd):

    access = True
    fields = ['title']
    title = MSG(u'Ajouter une application')


    def action(self, resource, context, form):
        proxy = super(Workgroup_NewInstance, self)
        goto = proxy.action(resource, context, form)
        workgroup = resource.get_resource(form['name'])
        # Set default language
        accept = context.accept_language
        ws_languages = context.root.get_value('website_languages')
        # FIXME
        current_language = 'en'
        #current_language = accept.select_language(ws_languages)
        #workgroup.set_value('website_languages', (current_language,))
        # Set title in current language
        workgroup.set_value('title', form['title']['en'], language=current_language)
        # Come back
        msg = MSG_NEW_WORKGROUP
        return context.come_back(msg, goto)



class Workgroup_View(AutoTable):

    access = 'is_allowed_to_edit'
    title = MSG(u"Manage your client space")

    # FIXME
    # template = '/ui/goodforms/workgroup/view.xml'
    base_classes = ('Application', )
    search_template = None

    table_fields = ['form', 'subscribed', 'max_users', 'file', 'ctime']
    table_actions = []

    # Fields
    form = Fake_Field


    def get_item_value(self, resource, context, item, column):
        if column == 'form':
            return item.get_title(), item.abspath
        elif column == 'subscribed':
            return len(list(item.get_forms()))
        elif column == 'file':
            parameters = item.get_resource('parameters')
            return (parameters.get_value('filename') or u"Source",
                    '{0}/;download'.format(context.get_link(parameters)))
        # Ok
        proxy = super(Workgroup_View, self)
        return proxy.get_item_value(resource, context, item, column)



class Workgroup_Edit(AutoEdit):

    title = MSG(u"Edit Title, Logo and CSS")
    fields = ['favicon', 'logo', 'style']
