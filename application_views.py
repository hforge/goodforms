# -*- coding: UTF-8 -*-
# Copyright (C) 2010 Hervé Cauwelier <herve@itaapy.com>
# Copyright (C) 2018 Nicolas Deram <nderam@gmail.com>
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
from email.utils import parseaddr
import traceback

# Import from itools
from itools.core import freeze
from itools.datatypes import Unicode
from itools.gettext import MSG
from itools.web import INFO, ERROR, STLView

# Import from ikaaro
from ikaaro.autoadd import AutoAdd
from ikaaro.autoedit import AutoEdit
from ikaaro.fields import Char_Field
from ikaaro.views import AutoTable

# Import from here
from buttons import AddUsersButton, Remove_BrowseButton
from datatypes import EmailField


INFO_NEW_APPLICATION = INFO(u'Your application is created !')
INFO_NEW_APPLICATION_WITH_ERRORS = INFO(u'Your application is created but '
                                        u'theres errors')
MSG_APPLICATION_TITLE = MSG(u'''<span class="application-title">Title of your
application:</span> {title}''', format='replace_html')


class Applications_View(AutoTable):

    title = MSG(u'Applications')
    base_classes = ('application',)
    table_fields = ['checkbox', 'title', 'subscription', 'nb_answers', 'ctime']
    table_actions = [Remove_BrowseButton]

    # Fields
    nb_answers = Char_Field(title=MSG(u'Nb answers'))

    def get_item_value(self, resource, context, item, column):
        if column == 'nb_answers':
            return item.get_n_forms()
        elif column == 'ctime':
            return context.format_datetime(item.get_value('ctime'))
        # Proxy
        proxy = super(Applications_View, self)
        return proxy.get_item_value(resource, context, item, column)



class Application_NewInstance(AutoAdd):

    fields = ['title', 'subscription', 'data']
    goto_view = None
    automatic_resource_name = True

    def action(self, resource, context, form):
        child = self.make_new_resource(resource, context, form)
        if child is None:
            return
        errors = None
        try:
            errors = child.load_ods_file(form['data'], context)
        except ValueError, e:
            context.message = ERROR(u'Cannot load: {x}').gettext(x=unicode(e))
            return
        except Exception:
            # FIXME (just for debug)
            print traceback.format_exc()
            pass
        if errors:
            msg = INFO_NEW_APPLICATION_WITH_ERRORS
        else:
            msg = INFO_NEW_APPLICATION
        goto = str(child.abspath)
        return context.come_back(msg, goto)



class Application_Edit(AutoEdit):

    title = MSG(u'Edit my form application')
    fields = ['title', 'subscription']



class Application_EditODS(AutoEdit):

    title = MSG(u'Change ODS file')
    fields = ['data']

    def action(self, resource, context, form):
        # Check edit conflict
        self.check_edit_conflict(resource, context, form)
        if context.edit_conflict:
            return
        errors = resource.load_ods_file(form['data'], context)
        if errors:
            msg = INFO_NEW_APPLICATION_WITH_ERRORS
        else:
            msg = INFO_NEW_APPLICATION
        # Ok
        goto = str(resource.abspath)
        return context.come_back(msg, goto)



class Application_Register(STLView):
    access = 'is_allowed_to_edit'
    title = MSG(u"Subscribe Users")
    template = '/ui/goodforms/application_register.xml'

    schema = freeze({
        'new_users': Unicode})
    actions = freeze([AddUsersButton])


    def get_page_title(self, resource, context):
        title = resource.get_page_title()
        return MSG_APPLICATION_TITLE.gettext(title=title)


    def get_actions_namespace(self, resource, context):
        actions = []
        for button in self.actions:
            actions.append(button(resource=resource, context=context))
        return actions


    def get_namespace(self, resource, context):
        proxy = super(Application_Register, self)
        namespace = proxy.get_namespace(resource, context)
        #namespace['menu'] = resource.menu.GET(resource, context)
        namespace['title'] = self.title
        namespace['n_forms'] = resource.get_n_forms()
        namespace['new_users'] = context.get_form_value('new_users')
        namespace['actions'] = self.get_actions_namespace(resource, context)
        namespace.update(resource.get_stats())
        return namespace


    def action_add_users(self, resource, context, form):
        new_users = form['new_users'].strip()
        users = resource.get_resource('/users')
        root = context.root
        added = []
        for lineno, line in enumerate(new_users.splitlines()):
            lastname, email = parseaddr(line)
            try:
                email = email.encode('utf-8')
            except UnicodeEncodeError:
                email = None
            if not email or not EmailField.is_valid(email):
                context.commit = False
                message = ERROR(u"Unrecognized line {lineno}: {line}")
                context.message = message.gettext(lineno=lineno+1, line=line)
                return
            if type(lastname) is str:
                lastname = unicode(lastname)
            # Is the user already known?
            user = root.get_user_from_login(email)
            if user is None:
                # Register the user
                user = users.set_user(**{'email': email, 'lastname': lastname})
            resource.subscribe_user(user)
            added.append(user.name)

        if not added:
            context.message = ERROR(u"No user added.")
            return

        context.body['new_users'] = u""

        message = INFO(u"{n} user(s) added.")
        context.message = message.gettext(n=len(added))
