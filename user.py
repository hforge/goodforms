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

# Import from itools
from itools.gettext import MSG
from itools.web import get_context

# Import from ikaaro
from ikaaro.emails import send_email
from ikaaro.fields import Text_Field
from ikaaro.users import User, Users

# Import from goodforms
from user_views import User_EditAccount


class GoodFormsUser(User):

    class_id = 'user'

    class_description = MSG(u'User')

    # Fields
    company = Text_Field(indexed=True, stored=True)

    # Views
    edit_account = User_EditAccount()



class GoodFormsUserFolder(Users):

    class_id = 'users'

    def set_user(self, **kw):
        # Register the user
        user = self.make_resource(None, GoodFormsUser, **kw)
        # Send email to the new user
        if user:
            user.update_pending_key()
            email_id = 'user-ask-for-confirmation'
            send_email(email_id, get_context(), kw['email'], user=user)
        # Ok
        return user
