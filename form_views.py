# -*- coding: UTF-8 -*-
# Copyright (C) 2009 Taverne Sylvain <sylvain@itaapy.com>
# Copyright (C) 2009-2010 Hervé Cauwelier <herve@itaapy.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Import from the Standard Library
from datetime import datetime
from decimal import InvalidOperation

# Import from itools
from itools.csv import CSVFile
from itools.core import merge_dicts, freeze
from itools.core import is_prototype
from itools.datatypes import String, Enumerate
from itools.gettext import MSG
from itools.log import log_debug
from itools.web import BaseView, STLView, INFO, ERROR

# Import from agitools
from agitools.autotable import AutoTable

# Import from goodforms
from buttons import InputControlLink
from buttons import ExportODSButton, ExportXLSButton
from buttons import SaveButton
from datatypes import Numeric, FileImage
from utils import get_page_number, force_encode, is_print, set_print
from widgets import is_mandatory_filled
from workflow import WorkflowState, NOT_REGISTERED, PENDING, FINISHED, EXPORTED
from customization import custom_flag
from rw import ODSWriter, XLSWriter

# Messages
MSG_APPLICATION_TITLE = MSG(u'<span class="application-title">Title of your application:</span> {title}', format='replace_html')
ERR_INVALID_FIELDS = ERROR(u"The following fields are invalid: {fields}.", format='replace_html')
ERR_MANDATORY_FIELDS = ERROR(u"The following fields are mandatory: {fields}.", format='replace_html')
ERR_BAD_SUMS = ERROR(u"The following sums are invalid: {fields}.", format='replace_html')
MSG_SAVED = INFO(u'The page is saved. Check your input in the <a href=";send">Input Control</a> tab.', format='html')
MSG_FINISHED = INFO(u"Your form is finished. Your correspondent has been informed.")
MSG_EXPORTED_ITAAPY = ERROR(u'To export to a SQL database, contact the administrator', format='html')
ERR_INVALID_FORMULA = ERROR(u"{name} is not equal to {formula}")
ERR_MANDATORY_FIELD = ERROR(u"{name} is mandatory")
ERR_INVALID_FIELD = ERROR(u"{name} is invalid")
ERR_NO_DATA = ERROR(u"No data to collect for now.")
ERR_NO_MORE_ALLOWED = ERROR(u'You have reached the maximum allowed users. <a href="./;order">Buy new credits</a> if you want to add more users.', format='html')
ERR_PASSWORD_MISSING = ERROR(u"The password is missing.")
ERR_BAD_EMAIL = ERROR(u"The given username is not an e-mail address.")
ERR_SUBSCRIPTION_FULL = ERROR(u"No more users are allowed to register.")
ERR_NOT_ALLOWED = ERROR(u"You are not allowed to register.")
ERR_ALREADY_REGISTERED = ERROR(u"You are already registered. Log in using your password.")
MSG_APPLICATION_TITLE = MSG(u'<span class="application-title">Title of your application:</span> {title}', format='replace_html')
MAILTO_SUBJECT = MSG(u'{workgroup_title}, form "{application_title}"')
MAILTO_BODY = MSG(u'Please fill in the form "{application_title}" available here:\r\n <{application_url}>.\r\n')


class Single(String):

    @classmethod
    def decode(cls, data):
        if type(data) is str:
            return data.strip()
        return data


Multiple = Single(multiple=True)



class Form_View(STLView):

    access = 'is_allowed_to_view'
    access_POST = 'is_allowed_to_edit'
    template = '/ui/goodforms/form/view.xml'
    title = MSG(u"Start filling")
    schema = freeze({
        'page_number': String})
    hidden_fields = []
    #toolbar = freeze([
    #    InputControlLink, PagePrintLink, FormPrintLink, SaveButton])
    toolbar = freeze([
        InputControlLink, SaveButton])
    actions = freeze([SaveButton])
    styles = ['/ui/goodforms/chosen.css']


    def get_page_title(self, resource, context):
        return resource.get_form_title()


    def get_hidden_fields(self, resource, context):
        schema = resource.get_schema()
        handler = resource.get_form().handler
        return [{
            'name': field,
            'value': handler.get_value(field, schema)}
                for field in self.hidden_fields
                if field[0] == self.page_number]


    def get_menu(self, resource, context):
        menu = []
        view_name = context.view_name or 'pageA'
        view_name = view_name.lower()
        for formpage in resource.get_formpages():
            menu.append({
                'title': formpage.get_title(),
                'href': ';page%s' % get_page_number(formpage.name),
                'class': 'active' if formpage.name == view_name else None})
        if len(menu) == 1:
            return []
        return menu


    def is_skip_print(self, resource, context):
        return False


    def get_toolbar_namespace(self, resource, context, readonly):
        actions = []
        for button in self.toolbar:
            actions.append(button(resource=resource, context=context,
                readonly=readonly, page_number=self.page_number))
        return actions


    def get_actions_namespace(self, resource, context, readonly):
        actions = []
        for button in self.actions:
            actions.append(button(resource=resource, context=context,
                readonly=readonly))
        return actions


    def get_namespace(self, resource, context):
        try:
            # Return from POST
            context.bad_types
        except AttributeError:
            # Fresh GET: not bad yet
            context.bad_types = set()
        skip_print = self.is_skip_print(resource, context)
        if is_print(context):
            skip_print = True
        readonly = not context.root.is_allowed_to_edit(context.user, resource)
        formpage = resource.get_formpage(self.page_number)
        namespace = formpage.get_namespace(resource, self, context,
                skip_print=skip_print, readonly=readonly)
        namespace['hidden_fields'] = self.get_hidden_fields(resource,
                context)
        namespace['application_menu'] = 'XXX'
        namespace['menu'] = self.get_menu(resource, context)
        namespace['toolbar'] = self.get_toolbar_namespace(resource, context,
                readonly)
        namespace['actions'] = self.get_actions_namespace(resource, context,
                readonly)
        return namespace

    def raw_action(self, resource, context, form):
        """ Simple version of action to quickly preload form without any check.
        page_number is unused (should be NOPAGE)
        """
        schema, pages = resource.get_schema_pages()
        fields = resource.get_fields(schema)
        handler = resource.get_form().handler
        # First save everything even invalid
        for field in fields:
            if context.get_form_value(field) is None:
                continue
            datatype = schema[field]
            value = fields[field]
            # Avoid "TypeError: issubclass() arg 1 must be a class"
            if isinstance(datatype, Numeric):
                pass
            elif issubclass(datatype, FileImage):
                # Delete existing file
                if context.get_form_value(field + '_delete'):
                    resource.parent.del_resource(value, ref_action='force')
                    fields[field] = ''
                    handler.set_value(field, '', schema)
            # Decode form data
            if context.get_form_value(field) is not None:
                # First the raw data
                if datatype.multiple:
                    data = context.get_form_value(field, type=Multiple)
                else:
                    data = context.get_form_value(field, type=Single)
                # Then the decoded value
                try:
                    value = datatype.decode(data)
                except Exception:
                    # Keep invalid values
                    value = data
                # Avoid "TypeError: issubclass() arg 1 must be a class"
                if isinstance(datatype, Numeric):
                    pass
                elif issubclass(datatype, FileImage):
                    # Load file
                    value = resource.save_file(*data)
            fields[field] = value
            handler.set_value(field, value, schema)

        # No Validity Checks Here !

        # Reindex
        context.database.change_resource(resource)
        # Transmit list of errors when returning GET
        context.message = MSG_SAVED
        # if resource.get_workflow_state() == EMPTY:
        resource.set_workflow_state(PENDING)

    def action(self, resource, context, form):
        schema, pages = resource.get_schema_pages()
        fields = resource.get_form_fields(schema)
        page_number = form['page_number']
        # Detect special page number for raw data pre loading
        if page_number == 'NOPAGE':
            return self.raw_action(resource, context, form)
        form = resource.get_form()
        handler = form.get_value('data')
        if not handler:
            # XXX FIXME WE SHOULD INIT HANDLER
            form.set_value('data', '')
            handler = form.get_value('data')
        formpage = resource.get_formpage(page_number)

        # First save everything even invalid
        for field in formpage.get_page_fields():
            datatype = schema[field]
            value = fields[field]
            # Avoid "TypeError: issubclass() arg 1 must be a class"
            if isinstance(datatype, Numeric):
                pass
            elif issubclass(datatype, FileImage):
                # Delete existing file
                if context.get_form_value(field + '_delete'):
                    resource.parent.del_resource(value, ref_action='force')
                    fields[field] = ''
                    handler.set_value(field, '', schema)
            # Decode form data
            if context.get_form_value(field) is not None:
                # First the raw data
                if datatype.multiple:
                    data = context.get_form_value(field, type=Multiple)
                else:
                    data = context.get_form_value(field, type=Single)
                # Then the decoded value
                try:
                    value = datatype.decode(data)
                except Exception:
                    # Keep invalid values
                    value = data
                # Avoid "TypeError: issubclass() arg 1 must be a class"
                if isinstance(datatype, Numeric):
                    pass
                elif issubclass(datatype, FileImage):
                    # Load file
                    value = resource.save_file(*data)
            fields[field] = value
            handler.set_value(field, value, schema)

        # Then check bad types
        invalid = []
        mandatory = []
        bad_sums = []
        for field in formpage.get_page_fields():
            computed = False
            datatype = schema[field]
            if resource.is_disabled_by_type(field, schema, datatype):
                continue
            if resource.is_disabled_by_dependency(field, schema, fields):
                continue
            # Raw data
            if datatype.multiple:
                data = context.get_form_value(field, type=Multiple)
            else:
                data = context.get_form_value(field, type=Single)
            # Decoded value
            value = fields[field]
            # Compute formula and compare
            if datatype.formula:
                try:
                    expected = datatype.sum(datatype.formula, schema,
                            # Raw form, not the filtered one
                            context.get_form())
                except InvalidOperation:
                    expected = None
                # Result given
                if data and value != expected:
                    # What we got was OK so blame the user
                    if expected is not None:
                        log = "field {0!r} data {1!r} value {2!r} bad sum"
                        log_debug(log.format(field, data, value))
                        if field not in bad_sums:
                            bad_sums.append(field)
                # Result deduced
                else:
                    # Got it right!
                    if expected is not None:
                        value = expected
                        # Fill the form
                        fields[field] = value
                        handler.set_value(field, value, schema)
                    # Got it wrong!
                    else:
                        log = "field {0!r} data {1!r} value {2!r} bad sum"
                        log_debug(log.format(field, data, value))
                        if field not in bad_sums:
                            bad_sums.append(field)
                computed = True
            # Mandatory
            if not data and not computed and datatype.mandatory:
                log = "field {0!r} data {1!r} value {2!r} mandatory"
                log_debug(log.format(field, data, value))
                mandatory.append(field) if field not in mandatory else None
            # Invalid (0008102 and mandatory -> and filled)
            elif data and ((type(data) == type("") and not datatype.is_valid(data))
                           or not datatype.is_valid(data)):
                try:
                    test = datatype.is_valid(data.decode('utf-8'))
                except:
                    try:
                        test = datatype.is_valid([x.decode('utf-8') for x in data])
                    except:
                        test = False
                if not test:
                    log = "field {0!r} data {1!r} value {2!r} invalid"
                    log_debug(log.format(field, data, value))
                    if field not in invalid:
                        invalid.append(field)
            # Avoid "TypeError: issubclass() arg 1 must be a class"
            if isinstance(datatype, Numeric):
                pass
            elif issubclass(datatype, Enumerate):
                # Detect unchecked checkboxes
                if not is_mandatory_filled(datatype, field, value, schema,
                        fields, context):
                    log = "field {0!r} data {1!r} value {2!r} not filled"
                    log_debug(log.format(field, data, value))
                    if field not in mandatory:
                        mandatory.append(field)

        # Reindex
        context.database.change_resource(resource)
        # Transmit list of errors when returning GET
        pattern = u'<a href="#field_{name}">{name}</a>'
        messages = []
        bad_types = set()
        for fields, message in [
                (invalid, ERR_INVALID_FIELDS),
                (mandatory, ERR_MANDATORY_FIELDS),
                (bad_sums, ERR_BAD_SUMS)]:
            if fields:
                bad_types.update(fields)
                fields = [pattern.format(name=f) for f in sorted(fields)]
                messages.append(message.gettext(fields=", ".join(fields)))
        if messages:
            context.bad_types = bad_types
            context.message = messages
        else:
            context.message = MSG_SAVED
        # FIXME
        # if resource.get_workflow_state() == EMPTY:
        #resource.set_workflow_state(PENDING)



class Form_Send(STLView):

    access = 'is_allowed_to_view'
    access_POST = 'is_allowed_to_edit'
    template = '/ui/goodforms/form/send.xml'
    title = MSG(u"Input Control")
    query_schema = freeze({
        'view': String})


    def get_page_title(self, resource, context):
        return resource.get_form_title()


    def get_namespace(self, resource, context):
        namespace = {}
        namespace['first_time'] = resource.is_first_time()
        # Errors
        errors = []
        warnings = []
        infos = []
        # Invalid fields
        for name, datatype, reason in resource.get_invalid_fields():
            if reason == 'sum_invalid':
                title = ERR_INVALID_FORMULA.gettext(name=name, formula=datatype.formula)
            elif reason == 'mandatory':
                title = ERR_MANDATORY_FIELD.gettext(name=name)
            else:
                if custom_flag('hide_invalid_empty'):
                    # maybe empty field
                    if datatype.multiple:
                        data = context.get_form_value(name, type=Multiple)
                    else:
                        data = context.get_form_value(name, type=Single)
                    if not data:
                        continue
                title = ERR_INVALID_FIELD(name=name)
            page = datatype.pages[0]
            if page == '' or page == '_':
                page = name.replace('_', '')[0]
            info = {
                    'number': name,
                    'title': title,
                    'href': ';page{page}#field_{name}'.format(
                        page=page, name=name),
                    'debug': str(type(datatype))}
            if datatype.mandatory:
                errors.append(info)
            else:
                warnings.append(info)
        # Failed controls
        for control in resource.get_failed_controls(context):
            control['href'] = ';page%s#field_%s' % (control['page'],
                    control['variable'])
            if control['level'] == '2':
                errors.append(control)
            else:
                warnings.append(control)
        # Informative controls
        for control in resource.get_info_controls(context):
            if control['page'] == '' or control['page'] == '_':
                control['page'] = control['variable'].replace('_', '')[0]
            control['href'] = ';page%s#field_%s' % (control['page'],
                    control['variable'])
            infos.append(control)
        namespace['controls'] = {
                'errors': errors,
                'warnings': warnings,
                'infos': infos}
        # ACLs
        is_allowed_to_export = True
        namespace['is_allowed_to_export'] = is_allowed_to_export
        # State
        namespace['statename'] = statename = resource.get_workflow_state()
        namespace['form_state'] = WorkflowState.get_value(
                resource.get_workflow_state())
        # Transitions
        namespace['can_send'] = statename == PENDING and not errors
        namespace['can_export'] = is_allowed_to_export and not errors
        # Debug
        namespace['debug'] = context.get_form_value('debug')
        # Print
        namespace['skip_print'] = is_print(context)
        return namespace


    def action_send(self, resource, context, form):
        """Ce qu'il faut faire quand le formulaire est soumis.
        """
        resource.set_workflow_state(FINISHED)

        # Notification e-mail
        application = resource.parent
        workgroup = application.parent
        subject = MSG(u"[GoodForms - {workgroup_title}] Form finished").gettext(
                workgroup_title=workgroup.get_title())
        stats = application.get_stats()
        user = context.user
        text = MSG(u"""\
{user_title} <{user_email}> finished to fill in the "{application_title}" form.

Summary of the "{application_title}" campaign:
- {registered_users} registered users out of {available_users} available;
- {unconfirmed_users} not registered;
- {empty_forms} empty forms;
- {pending_forms} pending forms;
- {finished_forms} finished forms.""").gettext(
                user_title=user.get_title(),
                user_email=user.get_value('email'),
                application_title=application.get_title(), **stats)

        # Send notification to workgroup members
        root = context.root
        users = resource.get_resource('/users')
        for username in workgroup.get_value('members'):
            member = users.get_resource(username)
            to_addr = (member.get_title(), member.get_value('email'))
            root.send_email(to_addr, subject, text=text,
                    subject_with_host=False)

        context.message = MSG_FINISHED


    def action_export(self, resource, context, form):
        """Ce qu'il faut faire quand le formulaire est exporté.
        """
        resource.set_workflow_state(EXPORTED)

        # XXX
        context.commit = False
        context.message = MSG_EXPORTED_ITAAPY



class Form_Export(BaseView):

    access = 'is_allowed_to_view'
    title = MSG(u"Download form")


    def GET(self, resource, context):
        encoding = 'cp1252'
        # FIXME
        #if not resource.is_ready():
        #    msg = MSG(u"Your form is not finished yet.")
        #    return context.come_back(msg, goto='/')
        # construct the csv
        csv = CSVFile()
        csv.add_row(["Chapitre du formulaire", "rubrique", "valeur"])
        schema = resource.get_schema()
        form = resource.get_form()
        handler = resource.get_value('data')
        for name, datatype in sorted(schema.iteritems()):
            if name in ('ctime', 'mtime'):
                continue
            value = handler.get_value(name, schema)
            data = force_encode(value, datatype, encoding)
            if type(data) is not str:
                raise ValueError, str(type(datatype))
            csv.add_row([datatype.pages[0], name, data])
        # Return as CSV
        context.set_content_type('text/comma-separated-values')
        context.set_content_disposition('attachment', filename="%s.csv" % (resource.name))
        # Ok
        return csv.to_str(separator=';')



class Form_Print(STLView):

    access = 'is_allowed_to_view'
    title=MSG(u"Print form")
    template = '/ui/goodforms/form/print.xml'
    styles = ['/ui/goodforms/print.css']
    pages = []


    def get_page_title(self, resource, context):
        return resource.get_form_title()


    def get_namespace(self, resource, context):
        set_print(context)
        context.bad_types = set()
        forms = []
        for page_number in resource.get_page_numbers():
            formpage = resource.get_formpage(page_number)
            view = getattr(resource, 'page%s' % page_number)
            ns = merge_dicts(formpage.get_namespace(resource, view, context,
                             skip_print=True), title=formpage.get_title())
            forms.append(ns)
        namespace = {}
        namespace['forms'] = forms
        return namespace




class Forms_View(AutoTable):

    title = MSG(u"Forms answers")

    # Search Form
    search_schema = {}
    search_fields = []

    # Configuration
    base_classes = ('form',)

    # Table
    table_fields = ['checkbox', 'name', 'form_state', 'mtime']

    table_actions = freeze([ExportODSButton, ExportXLSButton])


    def get_page_title(self, resource, context):
        title = resource.get_page_title()
        return MSG_APPLICATION_TITLE.gettext(title=title)



    def get_item_value(self, resource, context, item, column):
        if column == 'name':
            return (item.name, context.get_link(item))
        # Proxy
        proxy = super(Forms_View, self)
        return proxy.get_item_value(resource, context, item, column)


    def action_export(self, resource, context, form, writer_cls=ODSWriter):
        name = MSG(u"{title} Users").gettext(title=resource.get_title())
        writer = writer_cls(name)

        header = [title.gettext() for column, title in self.table_columns]
        writer.add_row(header, is_header=True)
        results = self.get_items(resource, context)
        context.query['batch_size'] = 0
        for item in self.sort_and_batch(resource, context, results):
            row = []
            for column, title in self.table_columns:
                if column == 'state':
                    item_brain, item_resource = item
                    user = context.root.get_user(item_brain.name)
                    if (user is not None
                            and user.get_value('password') is None):
                        state = NOT_REGISTERED
                    else:
                        state = item_brain.workflow_state
                    value = WorkflowState.get_value(state)
                else:
                    value = self.get_item_value(resource, context, item,
                            column)
                if type(value) is tuple:
                    value = value[0]
                if type(value) is unicode:
                    pass
                elif is_prototype(value, MSG):
                    value = value.gettext()
                elif type(value) is str:
                    value = unicode(value)
                elif type(value) is datetime:
                    return context.format_datetime(value)
                elif value is None:
                    value = ''
                else:
                    raise NotImplementedError, str(type(value))
                row.append(value)
            writer.add_row(row)

        body = writer.to_str()

        context.set_content_type(writer_cls.mimetype)
        context.set_content_disposition('attachment',
                filename="{0}-users.{1}".format(resource.name,
                    writer_cls.extension))

        return body


    def action_export_xls(self, resource, context, form):
        return self.action_export(resource, context, form,
                writer_cls=XLSWriter)




class Forms_Export(BaseView):

    access = 'is_admin'
    title = MSG(u"Export Collected Data")
    query_schema = freeze({ 'format': String})

    def GET(self, resource, context):
        for form in resource.parent.get_forms():
            state = form.get_workflow_state()
            if state != 'private':
                break
        else:
            return context.come_back(ERR_NO_DATA)

        format = context.query['format']
        if format == 'xls':
            writer_cls = XLSWriter
        else:
            writer_cls = ODSWriter
        name = MSG(u"{title} Data").gettext(title=resource.get_title())
        writer = writer_cls(name)

        schema_resource = resource.get_resource('schema')
        schema, pages = schema_resource.get_schema_pages()
        # Main header
        header = [title.gettext()
                for title in (MSG(u"Form"), MSG(u"First Name"),
                    MSG(u"Last Name"), MSG(u"E-mail"), MSG(u"State"))]
        for name in sorted(schema):
            header.append(name.replace('_', ''))
        try:
            writer.add_row(header, is_header=True)
        except FormatError, exception:
            return context.come_back(ERROR(unicode(exception)))
        # Subheader with titles
        header = [""] * 5
        for name, datatype in sorted(schema.iteritems()):
            header.append(datatype.title)
        writer.add_row(header, is_header=True)
        # optionnaly add a header in results with goodforms type for each column:
        if custom_flag('header_data_type'):
            header = [""] * 5
            for name, datatype in sorted(schema.iteritems()):
                header.append(datatype.type)
            writer.add_row(header, is_header=True)
        users = resource.get_resource('/users')
        for form in resource.get_forms():
            user = users.get_resource(form.name, soft=True)
            if user:
                get_value = user.get_value
                email = get_value('email')
                firstname = get_value('firstname')
                lastname = get_value('lastname')
            else:
                email = ""
                firstname = ""
                lastname = form.name
            state = WorkflowState.get_value(form.get_workflow_state())
            state = state.gettext()
            row = [form.name, firstname, lastname, email, state]
            handler = form.handler
            for name, datatype in sorted(schema.iteritems()):
                value = handler.get_value(name, schema)
                if datatype.multiple:
                    value = '\n'.join(value.decode('utf-8')
                            for value in datatype.get_values(value))
                else:
                    data = force_encode(value, datatype, 'utf_8')
                    value = unicode(data, 'utf_8')
                row.append(value)
            writer.add_row(row)

        body = writer.to_str()

        context.set_content_type(writer.mimetype)
        context.set_content_disposition('attachment',
                filename="{0}.{1}".format(resource.name, writer.extension))

        return body
