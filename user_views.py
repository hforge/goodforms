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
from itools.core import merge_dicts, is_prototype, freeze
from itools.database import AndQuery, TextQuery
from itools.datatypes import String, Unicode
from itools.gettext import MSG
from itools.web import INFO, ERROR, get_context

# Import from ikaaro
from ikaaro.autoedit import AutoEdit
from ikaaro.buttons import Remove_BrowseButton
from ikaaro.folder_views import Folder_BrowseContent
from ikaaro.utils import get_base_path_query
from ikaaro.widgets import TextWidget

# Import from goodforms
from csv_views import Folder_CSV_Export, CSVExportFormatButton, CSVColumn


class User_ConfirmRegistration(AutoEdit):

    fields = ['company']


    def action(self, resource, context, form):
        proxy = super(User_ConfirmRegistration, self)
        proxy.action(resource, context, form)
        if is_prototype(context.message, ERROR):
            return

        # Company
        resource.set_value('company', form['company'])

        message = INFO(u'Operation successful! Welcome.')
        return context.come_back(message, goto='/;show')



class User_ChangePasswordForgotten(AutoEdit):
    pass



class User_EditAccount(AutoEdit):

    fields = ['company']



class UserFolder_BrowseContent(Folder_CSV_Export):
    title = MSG(u"Browse Users")

    search_template = '/ui/generic/browse_search.xml'
    search_schema = {
        'search_field': String,
        'search_term': Unicode}
    search_fields = freeze([
        ('username', MSG(u'Login')),
        ('lastname', MSG(u'Last Name')),
        ('firstname', MSG(u'First Name')),
        ('email', MSG(u'E-mail')),
        ('email_domain', MSG(u'E-mail Domain')),
        ('company', MSG(u"Company"))])

    table_columns = freeze([
        ('checkbox', None, False),
        ('icon', None, False),
        ('name', MSG(u"User Id"), True),
        ('lastname', MSG(u"Last Name"), True),
        ('firstname', MSG(u"First Name"), True),
        ('email', MSG(u"E-mail"), True),
        ('company', MSG(u"Company"), True),
        ('user_must_confirm', MSG(u"Confirmed"), True),
        ('email_domain', MSG(u"E-mail Domain"), True),
        ('mtime', MSG(u"Last Modified"), True)])
    table_actions = freeze([
        Remove_BrowseButton, CSVExportFormatButton(access='is_admin')])

    csv_columns = freeze([
        # Titles not translated for Gmail
        CSVColumn('lastname', title=u"Last Name"),
        CSVColumn('firstname', title=u"First Name"),
        CSVColumn('email', title=u"E-mail Address"),
        CSVColumn('user_must_confirm', title=u"Confirmed"),
        CSVColumn('email_domain', title=u"E-mail Domain"),
        CSVColumn('company', title=u"Company")])


    def get_search_namespace(self, resource, context):
        proxy = super(Folder_BrowseContent, self)
        return proxy.get_search_namespace(resource, context)


    def get_items(self, resource, context, *args):
        # Query
        query = AndQuery(*args)

        # Search in subtree
        path = resource.get_canonical_path()
        query.append(get_base_path_query(str(path)))

        search_term = context.query['search_term']
        if search_term:
            search_field = context.query['search_field']
            query.append(TextQuery(search_field, search_term))

        return context.root.search(query)


    def get_key_sorted_by_lastname(self):
        return self._get_key_sorted_by_unicode('lastname')


    def get_key_sorted_by_firstname(self):
        return self._get_key_sorted_by_unicode('firstname')


    def get_key_sorted_by_user_must_confirm(self):
        # TODO obsolete with index in 0.70
        root = get_context().root
        def key(item):
            resource = root.get_resource(item.abspath)
            return bool(resource.get_property('user_must_confirm'))
        return key


    def get_key_sorted_by_company(self):
        return self._get_key_sorted_by_unicode('company')


    def get_item_value(self, resource, context, item, column):
        proxy = super(UserFolder_BrowseContent, self)
        value = proxy.get_item_value(resource, context, item, column)
        if column == 'user_must_confirm':
            return MSG(u"No") if value else MSG(u"Yes")
        return value
