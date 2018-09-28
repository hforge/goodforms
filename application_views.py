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
import traceback

# Import from itools
from itools.gettext import MSG
from itools.web import INFO, ERROR

# Import from ikaaro
from ikaaro.autoadd import AutoAdd
from ikaaro.autoedit import AutoEdit

# Import from agitools
from agitools.autotable import AutoTable
from agitools.buttons import Remove_BrowseButton
from agitools.fields import Fake_Field


INFO_NEW_APPLICATION = INFO(u'Your application is created. You are now on the test form.')


class Applications_View(AutoTable):

    title = MSG(u'Applications')
    base_classes = ('Application',)
    table_fields = ['checkbox', 'title', 'subscription', 'nb_answers', 'ctime']
    table_actions = [Remove_BrowseButton]

    # Fields
    nb_answers = Fake_Field(title=MSG(u'Nb answers'))

    def get_item_value(self, resource, context, item, column):
        if column == 'nb_answers':
            return u'TODO' #TODO
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
        try:
            child.load_ods_file(form['data'], context)
        except ValueError, e:
            context.message = ERROR(u'Cannot load: {x}').gettext(x=unicode(e))
            return
        except Exception:
            # FIXME (just for debug)
            print traceback.format_exc()
            pass
        goto = str(child.abspath)
        return context.come_back(INFO_NEW_APPLICATION, goto)





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
        resource.load_ods_file(form['data'], context)
        # Ok
        context.message = MSG(u'Ok')
