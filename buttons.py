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

# Import from itools
from itools.core import proto_property
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.buttons import BrowseButton, Button
from ikaaro.utils import make_stl_template



class CreateButton(Button):

    access = True
    title = None
    css = 'button-create'



class ExportODSButton(BrowseButton):

    access = 'is_allowed_to_edit'
    name = 'export'
    title = MSG(u"Export This List in ODS Format")



class ExportXLSButton(ExportODSButton):

    name = 'export_xls'
    title = MSG(u"Export This List in XLS Format")



class AddUsersButton(Button):

    access = 'is_allowed_to_edit'
    name = "add_users"
    title = MSG(u"Add Users")



class SaveButton(Button):

    access = 'is_allowed_to_edit'
    title = MSG(u"Save")
    id = "form-submit"


    @proto_property
    def show(cls):
        if cls.readonly:
            return False
        return super(SaveButton, cls).show



class Link(Button):

    id = None
    href = None
    onclick = None
    template = make_stl_template('''
        <a id="${id}" href="${href}" class="button ${css}" title="${title}"
            onclick="${onclick}">${content}</a>''')



class InputControlLink(Link):

    access = 'is_allowed_to_view'
    id = "button-control"
    css = "button-control"
    href = ";send"
    content = MSG(u"Input Control")



class PagePrintLink(Link):

    access = 'is_allowed_to_view'
    id = "button-page-print"
    css = "button-print"
    href = "?view=print"
    title = MSG(u"Print (in a new window)")
    onclick = "return popup(this.href, 800, 600)"
    content = MSG(u"Print this page")



class FormPrintLink(PagePrintLink):

    id = "button-form-print"
    href = ";print?view=print"
    content = MSG(u"Print Form")



class Remove_BrowseButton(Button):

    access = 'is_allowed_to_remove'
    confirm = MSG(u'Êtes vous sûr ?')
    css = 'btn btn-danger'
    icon_class = 'fa-trash-o fa-white'
    name = 'remove'
    title = MSG(u'Supprimer')

    template = make_stl_template("""
        <button name="${action}" class="${css}" value="${name}"
            onclick="${onclick}">
          <i class="fa ${icon_class}"/> ${title}
        </button>""")

    @proto_property
    def show(self):
        context = self.context
        for item in self.items:
            if context.is_access_allowed(item, self):
                return True
        return False
