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


MSG_NEW_WORKGROUP = INFO(u'Your client space is created. You can add your logo.')
MSG_ERR_NOT_IMAGE = ERROR(u'Not an image or invalid image.')
MSG_BAD_PASSWORD = ERROR(u'You already have an account but your password did not match. Try <a href="/;login">log in</a> first.', format='html')


class Workgroup_NewInstance(AutoAdd):

    access = True
    fields = ['title', 'firstname', 'lastname', 'company', 'accept_terms_of_use']
    def get_namespace(self, resource, context):
        proxy = super(Workgroup_NewInstance, self)
        namespace = proxy.get_namespace(resource, context)
        namespace['before'] = MSG(u"""<p id="already-client">Already
            registered and you want to log in your client space? <a
            href="/;login">Click here</a>.</p>""", format='html')
        return namespace


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
        # Accept terms and condition
        workgroup.set_value('accept_terms_of_use', form['accept_terms_of_use'])
        # Set title in current language
        workgroup.set_value('title', form['title']['en'], language=current_language)
        # Set neutral banner
#        theme = workgroup.get_resource('theme')
#        style = theme.get_resource('style')
#        style.handler.load_state_from_string("""/* Header colors / Couleurs de la bannière */
##header { background-color: #ccc; }
##header #links a, #header #languages a { color: #333; }
##header #logo-title { color: #000; }
#
#/* Form pages menu / Menu des pages du formulaire */
##pages-menu { border-bottom: 1px solid #339; }
##pages-menu ul li a {
#  background-color: #339;
#  border-color: #339;
#}
##pages-menu ul li a:hover {
#  background-color: #ccc;
#  color: #fff;
#}
##pages-menu ul li.active a {
#  background-color: #fff;
#  color: #339;
#}
#
#/* Form titles / Titres dans les formulaires */
#td.section-header h2,
#td.section-header h3,
#td.section-header h4 {
#  color: #fff;
#  background-color: #339;
#}
#""")
        user = context.user
        if user is None:
            email = form['email']
            root = context.root
            user = root.get_user_from_login(email)
            password = form['password']
            if user is None:
                # Create user
                if password != form['password2']:
                    context.message = messages.MSG_PASSWORD_MISMATCH
                    context.commit = False
                    return
                users = resource.get_resource('/users')
                user = users.set_user(email, password)
                # Send e-mail with login
                wg_path = '{0}/;login'.format(context.get_link(workgroup))
                site_uri = context.uri.resolve(wg_path)
                user.send_workgroup_registration(context, email, site_uri,
                        password.decode('utf-8'))
            else:
                # Existing user
                if not user.authenticate(password):
                    context.message = MSG_BAD_PASSWORD
                    context.commit = False
                    return
            # Automatic login
            context.login(user)
        # Update user info
        # FIXME
        #for key in ('firstname', 'lastname', 'company'):
        #    if form[key]:
        #        user.set_value(key, form[key])
        # Set the user as workgroup member
        # 10/01/13: test as admin
        username = user.name
        #workgroup.set_user_role(username, 'admins')
        # Come back
        msg = MSG_NEW_WORKGROUP
        return context.come_back(msg, goto)



class Workgroup_View(AutoTable):

    access = 'is_allowed_to_edit'
    title = MSG(u"Manage your client space")

    # FIXME
    # template = '/ui/goodforms/workgroup/view.xml'
    base_classes = 'Application'
    search_template = None

    table_fields = ['form', 'subscribed', 'max_users', 'file', 'ctime']
    table_actions = []


    def get_item_value(self, resource, context, item, column):
        brain, item_resource = item
        if column == 'form':
            return brain.title, brain.name
        elif column == 'subscribed':
            return len(list(item_resource.get_forms()))
        elif column == 'file':
            parameters = item_resource.get_resource('parameters')
            return (parameters.get_value('filename') or u"Source",
                    '{0}/;download'.format(context.get_link(parameters)))
        elif column == 'ctime':
            return context.format_datetime(brain.ctime)
        proxy = super(Workgroup_View, self)
        return proxy.get_item_value(resource, context, item, column)



class Workgroup_Edit(AutoEdit):

    title = MSG(u"Edit Title, Logo and CSS")
    fields = ['favicon', 'logo', 'style']
