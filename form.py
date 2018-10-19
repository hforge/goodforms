# -*- coding: UTF-8 -*-
# Copyright (C) 2006 Luis Belmar Letelier <luis@itaapy.com>
# Copyright (C) 2006-2010 Hervé Cauwelier <herve@itaapy.com>
# Copyright (C) 2009 Taverne Sylvain <sylvain@itaapy.com>
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
from decimal import InvalidOperation

# Import from itools
from itools.core import freeze
from itools.datatypes import DateTime
from itools.fs import FileName
from itools.gettext import MSG
from itools.handlers import File as FileHandler
from itools.web import get_context

# Import from ikaaro
from ikaaro.autoadd import AutoAdd
from ikaaro.autoedit import AutoEdit
from ikaaro.config_common import NewResource_Local
from ikaaro.fields import Text_Field, File_Field
from ikaaro.folder import Folder
from ikaaro.folder_views import GoToSpecificDocument
from ikaaro.utils import generate_name

# Import from goodforms
from datatypes import Numeric, NumDecimal, FileImage, SqlEnumerate
from form_views import Forms_View, Form_View, Form_Send, Form_Export, Form_Print
from form_views import Forms_Export
from utils import SI, get_page_number, parse_control
from workflow import WorkflowState_Field, FINISHED


class FormHandler(FileHandler):

    def _load_state_from_file(self, file):
        """Load known values, the rest will be the default values.
        """
        raw_fields = {}
        for line in file.readlines():
            if ':' not in line:
                continue
            key, data = line.split(':', 1)
            raw_fields[key.strip()] = data.strip()
        self._raw_fields = raw_fields


    def to_str(self, encoding='UTF-8'):
        lines = [ '%s:%s\n' % x for x in self._raw_fields.iteritems() ]
        lines.sort()
        return ''.join(lines)


    ######################################################################
    # API
    def get_value(self, name, schema):
        datatype = schema[name]
        data = self._raw_fields.get(name)
        if data is None:
            return datatype.get_default()
        if datatype.multiple:
            values = []
            for data in data.split():
                try:
                    value = datatype.decode(data)
                except ValueError:
                    value = data
                values.append(value)
            return values
        try:
            value = datatype.decode(data)
        except ValueError:
            value = data
        return value


    def set_value(self, name, value, schema):
        datatype = schema[name]
        if datatype.multiple:
            datas = []
            for value in value:
                try:
                    data = datatype.encode(value)
                except ValueError:
                    # XXX
                    data = unicode(value).encode('UTF-8')
                datas.append(data)
            data = '|'.join(datas)
        else:
            try:
                data = datatype.encode(value)
            except ValueError:
                # XXX
                data = unicode(value).encode('UTF-8')
        self._raw_fields[name] = data
        self.set_changed()



class Form(Folder):

    class_id = 'form'
    class_title = MSG(u"Form")
    class_description = MSG(u'Form answer')
    class_views = ['edit', 'pageA', 'export', 'view_print', 'send']

    # Fields
    data = File_Field(title=MSG(u'Form'), class_handler=FormHandler)
    form_state = Text_Field(title=MSG(u'State'), indexed=True, stored=True)
    workflow = WorkflowState_Field


    def init_resource(self, *args, **kw):
        # Proxy
        proxy = super(Form, self)
        proxy.init_resource(*args, **kw)
        # init
        context = get_context()
        self.set_value('data', 'ctime:{0}'.format(context.timestamp))


    def __getattr__(self, name):
        """Vues des pages du formulaire dynamiques
        """
        page_number = get_page_number(name)
        page = self.get_formpage(page_number)
        if page is None:
            raise AttributeError, name
        return Form_View(page_number=page.get_page_number())


    ######################################################################
    # API
    def get_param_folder(self):
        """Return the folder resource where parameters are stored.
        """
        return self.parent.parent.get_resource('model')


    def get_pages_folder(self):
        return self.get_param_folder().get_resource('pages')


    def get_schema_resource(self):
        """Return the CSV schema resource.
        """
        return self.get_param_folder().get_resource('schema')


    def get_schema_pages(self):
        """Load the schema from the CSV.
        """
        return self.get_schema_resource().get_schema_pages()


    def get_schema(self):
        schema, pages = self.get_schema_pages()
        schema['ctime'] = DateTime
        return schema


    def get_pages(self):
        schema, pages = self.get_schema_pages()
        return pages


    def get_form_fields(self, schema):
        handler = self.get_form().get_value('data')
        fields = {}
        for name in schema:
            # XXX We should init handler
            if handler:
                value = handler.get_value(name, schema)
            else:
                value = u''
            fields[name] = value
        return fields


    def get_globals(self):
        return {'SI': SI}


    def get_locals(self, schema, fields):
        locals_ = {}
        for name, datatype in sorted(schema.iteritems()):
            value = fields[name]
            try:
                value = float(value)
            except:
                try:
                    value = float(value.replace(',', '.'))
                except:
                    pass
            if issubclass(datatype, Numeric):
                pass
            if value is None:
                value = 0.
            elif issubclass(datatype, SqlEnumerate):
                if datatype.multiple:
                    values = []
                    for value in value:
                        value = datatype.get_value(value)
                        if value is not None:
                            value = value.encode('utf_8')
                        values.append(value)
                    value = values
                else:
                    value = datatype.get_value(value)
                    if value is not None:
                        value = value.encode('utf_8')
            locals_[name] = value
        return locals_


    def get_floating_locals(self, schema, fields):
        locals_ = self.get_locals(schema, fields)
        for name, value in locals_.iteritems():
            if isinstance(value, Numeric):
                locals_[name] = NumDecimal(value.value)
        return locals_


    def get_controls_resource(self):
        """Return the CSV controls resource.
        """
        return self.get_param_folder().get_resource('controls')


    def get_controls(self):
        """Load the controls from the CSV.
        """
        return self.get_controls_resource().get_controls()


    def get_page_numbers(self):
        """Return the ordered list of form page numbers.
        """
        page_numbers = []
        folder = self.get_pages_folder()
        for name in folder.get_names():
            page_number = get_page_number(name)
            if page_number is None:
                continue
            page_numbers.append(page_number.lower())
        # TODO backport Scrib order
        return sorted(page_numbers)


    def get_formpages(self):
        folder = self.get_pages_folder()
        for page_number in self.get_page_numbers():
            yield folder.get_resource('page' + page_number.lower())


    def get_formpage(self, page_number):
        """Return the FormPage resource for this number of page.
        """
        if page_number is None:
            return None
        name = 'pages/page%s' % page_number.lower()
        return self.get_param_folder().get_resource(name, soft=True)


    def get_form(self):
        """Shortcut to find the root form in MultipleForm.
        """
        return self


    def get_form_title(self):
        param = self.get_param_folder()
        form_title = None
        user = self.get_resource('/users/' + self.name, soft=True)
        if user is not None:
            form_title = user.get_title()
        if form_title is None:
            form_title = self.get_title()
        msg = MSG(u"{application}: {form}")
        return msg.gettext(application=param.get_title(), form=form_title)


    ######################################################################
    # Security
    def get_workflow_state(self):
        # FIXME
        return 'pending'


    def is_ready(self):
        return self.get_workflow_state() == FINISHED


    def is_first_time(self):
        handler = self.get_form().get_value('data')
        if not handler:
            return True
        return handler.timestamp is None


    def is_disabled_by_type(self, name, schema, datatype):
        return False


    def is_disabled_by_dependency(self, name, schema, fields):
        dependency = schema[name].dependency
        if not dependency:
            return False
        globals_ = self.get_globals()
        locals_ = self.get_locals(schema, fields)
        try:
            return not eval(dependency, globals_, locals_)
        except (ZeroDivisionError, InvalidOperation, ValueError):
            return False


    @staticmethod
    def get_reverse_dependency(name, schema):
        return [dep_name
                for dep_name, dep_datatype in schema.iteritems()
                if name in dep_datatype.dependency]


    def get_dep_names(self, name, schema, iteration=0, max_dep_names=3):
        dep_names = []
        for dep_name in self.get_reverse_dependency(name, schema):
            dep_names.append(dep_name)
            if iteration < max_dep_names:
                dep_names.extend(self.get_dep_names(dep_name, schema,
                    iteration=iteration+1))
        return dep_names


    def get_invalid_fields(self, pages=freeze([]), exclude=freeze([''])):
        schema = self.get_schema()
        fields = self.get_form_fields(schema)
        for name in sorted(fields):
            if name in ('ctime', 'mtime'):
                continue
            if pages and name[0] not in pages:
                continue
            if name[0] in exclude:
                continue
            datatype = schema[name]
            if self.is_disabled_by_type(name, schema, datatype):
                continue
            if self.is_disabled_by_dependency(name, schema, fields):
                continue
            value = fields[name]
            is_valid = datatype.is_valid(datatype.encode(value))
            is_sum_valid = True
            if datatype.formula:
                sum = datatype.sum(datatype.formula, schema, fields)
                is_sum_valid = (sum is None or sum == value)
            if datatype.mandatory:
                # False or 0 must be valid
                if type(value) == type(""):
                    value = value.decode('utf-8')
                if unicode(value).strip() and is_valid and is_sum_valid:
                    continue
            else:
                if is_valid and is_sum_valid:
                    continue
            reason = None
            if not is_sum_valid:
                reason = 'sum_invalid'
            elif not is_valid:
                reason = 'invalid'
            elif datatype.mandatory:
                reason = 'mandatory'
            yield name, datatype, reason


    def get_controls_namespace(self, context, levels=freeze([]),
            pages=freeze([]), exclude=freeze([''])):
        schema = self.get_schema()
        fields = self.get_form_fields(schema)
        for num, title, expr, level, page, variable in self.get_controls():
            if not expr:
                continue
            if level not in levels:
                continue
            if pages and page not in pages:
                continue
            if page in exclude:
                continue
            if variable is not None:
                datatype = schema[variable]
                if self.is_disabled_by_type(variable, schema, datatype):
                    continue
            globals_ = self.get_globals()
            # Précision pour les informations statistiques
            if level == '0':
                locals_ = self.get_floating_locals(schema, fields)
            else:
                locals_ = self.get_locals(schema, fields)
            try:
                value = eval(str(expr), globals_, locals_)
            except ZeroDivisionError:
                # Division par zéro toléré
                value = None
            except (InvalidOperation, ValueError):
                # Champs vides tolérés
                value = None
            # Passed
            if value is True and '0' not in levels:
                continue
            # Le titre contient des formules
            if u'[' in title:
                expanded = []
                for is_expr, token in parse_control(title):
                    if not is_expr:
                        expanded.append(token)
                    else:
                        try:
                            value = eval(token, globals_, locals_)
                        except ZeroDivisionError:
                            value = None
                        expanded.append(unicode(value))
                title = u"".join(expanded)
            if value is True:
                value = MSG(u"True")
            elif value is False:
                value = MSG(u"False")
            elif isinstance(value, NumDecimal):
                try:
                    value = context.format_number(value.value)
                except InvalidOperation:
                    value = value.value
            yield {
                'number': num,
                'title': title,
                'level': level,
                'variable': variable,
                'page': page,
                'value': value,
                'debug': u'"{0}" = "{1}"'.format(expr, value)}


    def get_info_controls(self, context, pages=freeze([]),
            exclude=freeze([''])):
        for control in self.get_controls_namespace(context, levels=['0'],
                pages=pages, exclude=exclude):
            yield control


    def get_failed_controls(self, context, pages=freeze([]),
            exclude=freeze([''])):
        for control in self.get_controls_namespace(context,
                levels=['1', '2'], pages=pages, exclude=exclude):
            yield control


    def save_file(self, filename, mimetype, body):
        name, extension, language = FileName.decode(filename)
        parent = self.parent
        used = parent.get_names()
        #name = checkid(name) or 'invalid'
        name = generate_name(name, used)
        context = get_context()
        cls = context.database.get_resource_class(mimetype)
        metadata = {
                'format': mimetype,
                'filename': filename,
                'extension': extension}
        parent.make_resource(name, cls, body=body, **metadata)
        return name

    # Views
    edit = AutoEdit(fields=['title'])
    _fields = ['title']
    new_instance = AutoAdd(fields=_fields, automatic_resource_name=True)
    send = Form_Send()
    export = Form_Export()
    view_print = Form_Print()



class Forms(Folder):

    class_id = 'forms'
    class_title = MSG(u"Form answers")
    class_views = ['view', 'new_resource', 'export']
    class_icon_css = 'fa-user'

    def get_document_types(self):
        return [Form]


    ######################################################################
    # API
    def get_param_folder(self):
        """Return the folder resource where parameters are stored.
        """
        return self.parent.get_resource('model')


    def get_pages_folder(self):
        return self.get_param_folder().get_resource('pages')


    def get_schema_resource(self):
        """Return the CSV schema resource.
        """
        return self.get_param_folder().get_resource('schema')


    def get_schema_pages(self):
        """Load the schema from the CSV.
        """
        return self.get_schema_resource().get_schema_pages()


    def get_schema(self):
        schema, pages = self.get_schema_pages()
        schema['ctime'] = DateTime
        return schema


    def get_pages(self):
        schema, pages = self.get_schema_pages()
        return pages


    def get_controls_resource(self):
        """Return the CSV controls resource.
        """
        return self.get_param_folder().get_resource('controls')


    def get_controls(self):
        """Load the controls from the CSV.
        """
        return self.get_controls_resource().get_controls()


    # Views
    view = Forms_View
    new_resource = NewResource_Local(title=MSG(u'Create an answer to form'))
    export = Forms_Export
