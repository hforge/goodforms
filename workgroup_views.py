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
from itools.database import PhraseQuery
from itools.datatypes import Boolean, Unicode, Email, String
from itools.gettext import MSG
from itools.stl import stl
from itools.web import INFO, ERROR
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro import messages
from ikaaro.autoform import TextWidget, MultilineWidget, PasswordWidget
from ikaaro.autoform import ReadOnlyWidget, CheckboxWidget
from ikaaro.folder_views import Folder_BrowseContent
from ikaaro.resource_views import DBResource_Edit
from ikaaro.theme_views import Theme_Edit
from ikaaro.views_new import NewInstance

# Import from itws
from itws.feed_views import FieldsTableFeed_View
from itws.shop.order_views import OrderState_Template
from itws.shop.workflows import OrderStateEnumerate


# Import from goodforms
from application import Application
from autoform import ImagePathDataType, ImageSelectorWidget
from autoform import RecaptchaDatatype, captcha_schema, captcha_widgets
from base_views import IconsView


MSG_NEW_WORKGROUP = INFO(u'Your client space "{title}" is created. You can '
        u'add your logo.')
MSG_ERR_NOT_IMAGE = ERROR(u'Not an image or invalid image.')
MSG_BAD_PASSWORD = ERROR(u'You already have an account but your password '
        u'did not match. Try <a href="/;login">log in</a> first.',
        format='html')


class Workgroup_NewInstance(NewInstance):
    access = True
    schema = freeze(merge_dicts(
        NewInstance.schema,
        title=Unicode(mandatory=True),
        firstname=Unicode,
        lastname=Unicode,
        company=Unicode,
        accept_terms_of_use=Boolean(mandatory=True)))
    widgets = freeze([
        ReadOnlyWidget('cls_description'),
        TextWidget('title', title=MSG(u'Name of your client space'),
            tip=MSG(u'You can type the name of your company or '
                u'organization'))])
    goto_view = None

    anonymous_schema = freeze({
        'email': Email(mandatory=True),
        'password': String(mandatory=True),
        'password2': String(mandatory=True)})
    anonymous_widgets = freeze([
        TextWidget('email', title=MSG(u"Your e-mail address")),
        TextWidget('firstname', title=MSG(u"First Name")),
        TextWidget('lastname', title=MSG(u"Last Name")),
        TextWidget('company', title=MSG(u"Company")),
        PasswordWidget('password', title=MSG(u"Password")),
        PasswordWidget('password2', title=MSG(u"Repeat Password"))])

    terms_of_use_widget = CheckboxWidget('accept_terms_of_use',
             title=MSG(u'I have read and agree to the terms of use '
                       u'(<a href="/terms-and-conditions" '
                       u'title="Terms of use" target="_blank">Terms of use</a>)',
                       format='html'))


    def get_schema(self, resource, context):
        schema = self.schema
        if context.user is None:
            schema = freeze(merge_dicts(schema, self.anonymous_schema))
        if RecaptchaDatatype.is_required(context):
            schema = freeze(merge_dicts(schema, captcha_schema))
        return schema


    def get_widgets(self, resource, context):
        widgets = self.widgets
        if context.user is None:
            widgets = widgets + self.anonymous_widgets
        if RecaptchaDatatype.is_required(context):
            widgets = widgets + captcha_widgets
        # Terms of use widget
        widgets = widgets + [self.terms_of_use_widget]
        return widgets


    def get_value(self, resource, context, name, datatype):
        if name == 'email':
            value = context.get_query_value(name)
            if value:
                return value
        proxy = super(Workgroup_NewInstance, self)
        return proxy.get_value(resource, context, name, datatype)


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
        ws_languages = context.root.get_property('website_languages')
        current_language = accept.select_language(ws_languages)
        workgroup.set_property('website_languages', (current_language,))
        # Accept terms and condition
        workgroup.set_property('accept_terms_of_use',
                               form['accept_terms_of_use'])
        # Set title in current language
        workgroup.set_property('title', None)
        workgroup.set_property('title', form['title'],
                language=current_language)
        # Set neutral banner
        theme = workgroup.get_resource('theme')
        style = theme.get_resource('style')
        style.handler.load_state_from_string("""/* Header colors / Couleurs de la bannière */
#header { background-color: #ccc; }
#header #links a, #header #languages a { color: #333; }
#header #logo-title { color: #000; }

/* Form pages menu / Menu des pages du formulaire */
#pages-menu { border-bottom: 1px solid #339; }
#pages-menu ul li a {
  background-color: #339;
  border-color: #339;
}
#pages-menu ul li a:hover {
  background-color: #ccc;
  color: #fff;
}
#pages-menu ul li.active a {
  background-color: #fff;
  color: #339;
}

/* Form titles / Titres dans les formulaires */
td.section-header h2,
td.section-header h3,
td.section-header h4 {
  color: #fff;
  background-color: #339;
}
""")
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
        for key in ('firstname', 'lastname', 'company'):
            if form[key]:
                user.set_property(key, form[key])
        # Set the user as workgroup member
        # 10/01/13: test as admin
        username = user.name
        workgroup.set_user_role(username, 'admins')
        # Come back
        message = MSG_NEW_WORKGROUP(title=form['title'])
        return context.come_back(message, goto)



class Workgroup_Menu(IconsView):
    make_item = IconsView.make_item
    items = [make_item(icon='/ui/goodforms/images/download48.png',
              title=MSG(u"Download the Template"),
              description=MSG(u"Download this template and use it to "
                  u"define to design your form."),
              extra=MSG(u"""
<div id="choose-format">
  <span><a href="#" title="Close"
    onclick="$('#choose-format').hide(); return false">X</a></span>
  <ul>
    <li>Download <a href="/template/;download">ODS Version</a></li>
    <li>Download <a href="/template-xls/;download">XLS Version</a></li>
    <li><a href="/samples">More Examples</a></li>
  </ul>
</div>
<script type="text/javascript">
  $("#choose-format").hide();
</script>""", format='html'),
              url='#',
              onclick='$("#choose-format").show(); return false'),
             make_item(icon='/ui/goodforms/images/upload48.png',
              title=MSG(u"Create a Data Collection Application"),
              description=MSG(u"Uploading this spreadsheet file in GoodForms will generate in one click your data collection application."),
              url=';new_resource?type=Application'),
             make_item(icon='/ui/goodforms/images/logo48.png',
              title=MSG(u"Edit Title, Logo and CSS"),
              description=MSG(u"Configure your client space"),
              url=';edit'),
             make_item(icon='/ui/shop/images/orders.png',
              title=MSG(u"Manage my bills"),
              description=MSG(u"Manage my bills & buy new products"),
              url='./orders')]



class Workgroup_View(Folder_BrowseContent):
    access = 'is_allowed_to_edit'
    template = '/ui/goodforms/workgroup/view.xml'
    title = MSG(u"Manage your client space")
    search_template = None

    table_columns = freeze([
            ('form', MSG(u"Application")),
            ('subscribed', MSG(u"Subscribed Users")),
            ('max_users', MSG(u'Maximum users')),
            ('file', MSG(u"Source File")),
            ('ctime', MSG(u"Creation Date"))])
    table_actions = freeze([])


    def get_namespace(self, resource, context):
        # Menu
        resource.get_resource('theme')
        menu = Workgroup_Menu().GET(resource, context)

        # Batch
        batch = None
        items = self.get_items(resource, context)
        if items and self.batch_template is not None:
            template = resource.get_resource(self.batch_template)
            namespace = self.get_batch_namespace(resource, context, items)
            batch = stl(template, namespace)

        # Table
        table = None
        if batch:
            if self.table_template is not None:
                items = self.sort_and_batch(resource, context, items)
                template = resource.get_resource(self.table_template)
                namespace = self.get_table_namespace(resource, context,
                        items)
                table = stl(template, namespace)

        return {'menu': menu, 'batch': batch, 'table': table}


    def get_items(self, resource, context, *args):
        query = PhraseQuery('format', Application.class_id)
        proxy = super(Workgroup_View, self)
        return proxy.get_items(resource, context, query, *args)


    def sort_and_batch(self, resource, context, results):
        start = context.query['batch_start']
        size = context.query['batch_size']
        sort_by = context.query['sort_by']
        reverse = context.query['reverse']
        items = results.get_documents(sort_by=sort_by, reverse=reverse,
                                      start=start, size=size)

        # FIXME This must be done in the catalog.
        if sort_by == 'title':
            items.sort(cmp=lambda x,y: cmp(x.title, y.title))
            if reverse:
                items.reverse()

        # Access Control (FIXME this should be done before batch)
        root = context.root
        allowed_items = []
        for item in items:
            resource = root.get_resource(item.abspath)
            # On regarde mais sans toucher
            #ac = resource.get_access_control()
            #if ac.is_allowed_to_view(user, resource):
            allowed_items.append((item, resource))

        return allowed_items


    def get_item_value(self, resource, context, item, column):
        brain, item_resource = item
        if column == 'form':
            return brain.title, brain.name
        elif column == 'subscribed':
            return len(list(item_resource.get_forms()))
        elif column == 'file':
            parameters = item_resource.get_resource('parameters')
            return (parameters.get_property('filename') or u"Source",
                    '{0}/;download'.format(context.get_link(parameters)))
        elif column == 'ctime':
            return context.format_datetime(brain.ctime)
        proxy = super(Workgroup_View, self)
        return proxy.get_item_value(resource, context, item, column)



class Workgroup_Edit(Theme_Edit, DBResource_Edit):
    title = MSG(u"Edit Title, Logo and CSS")
    schema = freeze(merge_dicts(
        DBResource_Edit.schema,
        favicon=ImagePathDataType,
        logo=ImagePathDataType,
        style=String))
    widgets = freeze(
            [DBResource_Edit.widgets[0]]
            + [DBResource_Edit.widgets[1](title=MSG(u"Title (shown in "
                u"the banner if no logo)"))]
            + [ImageSelectorWidget('logo', action='add_logo',
                    title=MSG(u'Logo (shown in the banner)')),
                MultilineWidget('style', title=MSG(u"CSS"), rows=19,
                    cols=69)])


    def get_value(self, resource, context, name, datatype):
        if name == 'favicon':
            return ''
        elif name == 'logo':
            # Path must be resolved relative to here
            theme = resource.get_resource('theme')
            path = theme.get_property(name)
            if path == '':
                return ''
            logo = theme.get_resource(path)
            return resource.get_pathto(logo)
        elif name == 'style':
            style = resource.get_resource('theme/style')
            # FIXME links
            return style.handler.to_str()
        proxy = super(Workgroup_Edit, self)
        return proxy.get_value(resource, context, name, datatype)


    def set_value(self, resource, context, name, form):
        if name == 'favicon':
            return False
        elif name == 'logo':
            # Path must be saved relative to the theme
            path = form[name]
            theme = resource.get_resource('theme')
            if path == '':
                theme.set_property(name, '')
                return False
            logo = resource.get_resource(path)
            logo.set_workflow_state('public')
            theme.set_property(name, str(theme.get_pathto(logo)))
            return False
        elif name == 'style':
            style = resource.get_resource('theme/style')
            # FIXME links
            style.handler.load_state_from_string(form['style'])
            return False
        proxy = super(Workgroup_Edit, self)
        return proxy.set_value(resource, context, name, form)



class Workgroup_ViewOrders(FieldsTableFeed_View):

    title = MSG(u'Orders')
    access = 'is_allowed_to_view'

    sort_by = 'ctime'
    reverse = True
    batch_msg1 = MSG(u"There is 1 order")
    batch_msg2 = MSG(u"There are {n} orders")
    table_actions = []

    styles = ['/ui/shop/style.css']

    search_on_current_folder = True
    search_on_current_folder_recursive = False

    search_fields = []
    table_fields = ['checkbox', 'name', 'workflow_state',
                    'total_price', 'total_paid', 'ctime', 'bill']

    def get_item_value(self, resource, context, item, column):
        brain, item_resource = item
        if column in ('total_price', 'total_paid'):
            value = item_resource.get_property(column)
            return item_resource.format_price(value)
        elif column == 'name':
            return OrderState_Template(title=brain.name,
                link=context.get_link(item_resource), color='#BF0000')
        elif column == 'workflow_state':
            value = item_resource.get_statename()
            title = OrderStateEnumerate.get_value(value)
            return OrderState_Template(title=title,
                link=context.get_link(item_resource), color='#BF0000')
        elif column == 'bill':
            bill = item_resource.get_bill()
            if bill is None:
                return None
            return XMLParser("""
                    <a href="%s/;download">
                      <img src="/ui/icons/16x16/pdf.png"/>
                    </a>""" % context.get_link(bill))
        proxy = super(Workgroup_ViewOrders, self)
        return proxy.get_item_value(resource, context, item, column)


    @property
    def search_cls(self):
        from workgroup import Workgroup_Order
        return Workgroup_Order


    def get_items(self, resource, context, *args):
        query = PhraseQuery('is_order', True)
        proxy = super(Workgroup_ViewOrders, self)
        return proxy.get_items(resource, context, query)
