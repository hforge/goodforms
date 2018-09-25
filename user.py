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
from itools.core import merge_dicts, freeze
from itools.datatypes import Unicode, Boolean
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.fields import Text_Field, Boolean_Field
from ikaaro.users import User, Users

# Import from goodforms
from user_views import User_EditAccount, User_ConfirmRegistration
from user_views import User_ChangePasswordForgotten
from user_views import UserFolder_BrowseContent


class GoodFormsUser(User):

    # Fields
    company = Text_Field(indexed=True, stored=True)
    has_password = Boolean_Field(indexed=True)

    # Views
    edit_account = User_EditAccount()
    confirm_registration = User_ConfirmRegistration()
    change_password_forgotten = User_ChangePasswordForgotten()

    form_registration_text = MSG(u"""You are now registered as a user of {site_name}.

You can follow this link <{site_uri}> to access your form.

Your e-mail address {email} is your identifier.

Your password: {password}""")

    workgroup_registration_text = MSG(u"""You are now registered as a user of {site_name}.

You can follow this link <{site_uri}> to access your workgroup.

Your e-mail address {email} is your identifier.

Your password: {password}""")


    def get_catalog_values(self):
        values = super(GoodFormsUser, self).get_catalog_values()
        values['has_password'] = self.get_value('password') is not None
        return values


    def send_form_registration(self, context, email, site_uri, password):
        site_name = context.resource.get_site_root().get_title()
        text = self.form_registration_text.gettext(site_name=site_name,
                site_uri=site_uri, email=email, password=password.decode('utf-8'))
        context.root.send_email(email, self.registration_subject.gettext(),
                                text=text, encoding='ISO-8859-1')


    def send_workgroup_registration(self, context, email, site_uri,
            password):
        site_name = context.resource.get_site_root().get_title()
        text = self.workgroup_registration_text.gettext(site_name=site_name,
                site_uri=site_uri, email=email, password=password)
        context.root.send_email(email, self.registration_subject.gettext(),
                                text=text, encoding='ISO-8859-1')



class GoodFormsUserFolder(Users):

    class_views = ['view', 'browse_users', 'browse_content', 'edit']

    # Views
    browse_users = UserFolder_BrowseContent()
