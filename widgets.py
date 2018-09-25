# -*- coding: UTF-8 -*-
# Copyright (C) 2005  <jdavid@favela.(none)>
# Copyright (C) 2006 J. David Ibanez <jdavid@itaapy.com>
# Copyright (C) 2006 luis <luis@lucifer.localdomain>
# Copyright (C) 2006-2010 Hervé Cauwelier <herve@itaapy.com>
# Copyright (C) 2008 Henry Obein <henry@itaapy.com>
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

# Import from the Standard Library
from decimal import InvalidOperation

# Import from itools
from itools.core import is_prototype, merge_dicts
from itools.datatypes import XMLContent, XMLAttribute
from itools.gettext import MSG
from itools.handlers import checkid
from itools.log import log_warning
from itools.web import get_context

# Import from ikaaro
from ikaaro.widgets import RadioWidget
from ikaaro.file import Image
from ikaaro.utils import make_stl_template

# Import from goodforms
from datatypes import Numeric, Text, EnumBoolean, SqlEnumerate, NumDecimal, NumInteger
from datatypes import NumDate, NumTime, FileImage
from schema import Expression


NBSP = u"\u00a0".encode('utf8')
FIELD_PREFIX = u"#"


def is_mandatory_filled(datatype, name, value, schema, fields, context):
    if context.method != 'POST':
        return True
    if context.resource.is_disabled_by_dependency(name, schema, fields):
        return True
    if not datatype.mandatory:
        return True
    return value is not None



def make_element(tagname, attributes={}, content=u""):
    if is_prototype(content, MSG):
        content = content.gettext()
    element = [u"<", tagname]
    for key, value in attributes.iteritems():
        if value is None:
            continue
        if type(value) is list:
            value = u" ".join(value)
        elif is_prototype(value, MSG):
            value = value.gettext()
        element.extend((u" ", key, u'="', value, u'"'))
    if tagname in ('input', 'img'):
        element.extend((u"/>", content))
    else:
        element.extend((u">", content, u"</", tagname, u">"))
    return u"".join(element)



def check_errors(context, form, datatype, name, value, schema, fields,
        readonly, attributes, tabindex=None):
    attributes.setdefault(u"class", [])
    if name in context.bad_types:
        attributes[u"title"] = MSG(u"Bad value")
        attributes[u"class"].append(u"badtype")
    elif not is_mandatory_filled(datatype, name, value, schema, fields,
            context):
        attributes[u"title"] = MSG(u"Mandatory field")
        attributes[u"class"].append(u"mandatory")
    if form.is_disabled_by_dependency(name, schema, fields):
        attributes[u"disabled"] = u"disabled"
        #attributes[u"class"].append(u"disabled")
    if tabindex:
        attributes[u"tabindex"] = tabindex



def _choice_widget(context, form, datatype, name, value, schema, fields,
        readonly, container, container_attributes, choice, choice_attributes,
        choice_checked, multiline, tabindex):
    html = []

    # True -> '1' ; False -> '2'
    data = datatype.encode(value)

    if readonly:
        for option in datatype.get_namespace(data):
            attributes = merge_dicts(
                    choice_attributes,
                    value=option['name'],
                    disabled=u"disabled")
            attributes.setdefault(u"class", []).append(u"disabled")
            if option['selected']:
                attributes[choice_checked] = choice_checked
            value = option['value']
            if is_prototype(value, MSG):
                value = value.gettext()
            content = XMLContent.encode(value)
            input = make_element(choice, attributes, content)
            if multiline is True:
                # Une option par ligne
                html.append(make_element(u"div", content=input))
            else:
                html.append(input)
    else:
        if type(data) == type("") or type(data) == type(u""):
            try:
                data_tmp = data.decode("utf-8").split('|')
            except:
                data_tmp = data
        else:
            data_tmp = data
        for option in datatype.get_namespace(data_tmp):
            js = []
            opt_name = option['name']
            attributes = merge_dicts(choice_attributes, value=opt_name)
            if option['selected'] or data == option['name'].strip().encode('utf-8'):
                attributes[choice_checked] = choice_checked
            if form.is_disabled_by_dependency(name, schema, fields):
                attributes[u"disabled"] = u"disabled"
                attributes.setdefault(u"class", []).append(u"disabled")

            # 0005970: Le Javascript pour (dés)activer les autres champs
            dep_names = form.get_dep_names(name, schema)
            for dep_name in dep_names:
                dependency = schema[dep_name].dependency
                if not dependency:
                    continue
                # Add js action on simple boolean expressions. ie: "C11"
                if not Expression.is_simple(dependency):
                    # Authorized operators are "==", "=" and "in"
                    # ie:"C11=='others'", "C11='others'", "'others' in  C11"
                    if 'in' in dependency:
                        dep_value = dependency.split('in', 1)[0].strip()
                    elif '==' in dependency:
                        exclusive, dep_value = dependency.rsplit('==', 1)
                    elif '!=' in dependency:
                        exclusive, dep_value = dependency.rsplit('!=', 1)
                    else:
                        msg = 'K col operator unknown in "%s"' % dependency
                        log_warning(msg)
                        continue
                    if dep_value[:1] in ("u'" , 'u"'):
                        dep_value = dep_value[:2]
                    dep_value = (dep_value.replace("'", '').replace('"', ''))
                    #dep_value = checkid(dep_value)
                else:
                    dep_value = 'false'

                js_code = (
                    '$("input[name=\\"%s\\"][value=\\"%s\\"]")'
                    '.change(function(){switch_input($(this),"%s","%s");});'
                    % (name, opt_name, dep_name, dep_value))
                js.append(js_code)

            # 0005970 fin
            value = option['value']
            if is_prototype(value, MSG):
                value = value.gettext()
            content = XMLContent.encode(value)
            input = make_element(choice, attributes, content)
            if multiline is True:
                # Une option par ligne
                html.append(make_element(u"div", content=input))
            else:
                html.append(input)

            # Append JS code
            content = XMLContent.encode(u'\n'.join(js))
            attributes = {u'type': "text/javascript"}
            html.append(make_element(u'script', attributes, content))

    attributes = merge_dicts(
            container_attributes,
            id=u"field_{name}".format(name=name))
    check_errors(context, form, datatype, name, data, schema, fields,
            readonly, attributes, tabindex=None)
    return make_element(container, attributes, u"".join(html))



def radio_widget(context, form, datatype, name, value, schema, fields,
        readonly, tabindex=None):
    container = u"div"
    container_attributes = {}
    choice = u"input"
    choice_attributes = {
            u"id": u"field_{name}".format(name=name),
            u"type": u"radio",
            u"name": name}
    choice_checked = u"checked"
    # Oui/Non sur une seule ligne
    multiline = not issubclass(datatype, EnumBoolean)
    return _choice_widget(context, form, datatype, name, value, schema,
            fields, readonly, container, container_attributes, choice,
            choice_attributes, choice_checked, multiline, tabindex)



def checkbox_widget(context, form, datatype, name, value, schema, fields,
        readonly, tabindex=None):
    container = u"div"
    container_attributes = {}
    choice = u"input"
    choice_attributes = {
            u"id": u"field_{name}".format(name=name),
            u"type": u"checkbox",
            u"name": name}
    choice_checked = u"checked"
    # Oui/Non sur une seule ligne
    multiline = not issubclass(datatype, EnumBoolean)
    if type(value) == type([]):
        value = " ".join(value)
    return _choice_widget(context, form, datatype, name, value, schema,
            fields, readonly, container, container_attributes, choice,
            choice_attributes, choice_checked, multiline, tabindex)



def select_widget(context, form, datatype, name, value, schema, fields,
        readonly, tabindex=None):
    container = u"select"
    container_attributes = {
        u"name": name,
        u"class": "chosen-select"}
    choice = u"option"
    choice_attributes = {
	    u"name": name}
    choice_checked = u"selected"
    multiline = False
    return _choice_widget(context, form, datatype, name, value, schema,
            fields, readonly, container, container_attributes, choice,
            choice_attributes, choice_checked, multiline, tabindex)



def textarea_widget(context, form, datatype, name, value, schema, fields,
        readonly, tabindex=None):
    if readonly:
        attributes = {
            u"style": u"white-space: pre",
            u"class": u"readonly"}
        content = XMLContent.encode(value)
        return make_element(u"div", attributes, content)

    attributes = {
        u"id": u"field_{name}".format(name=name),
        u"name": name,
        u"rows": str(datatype.size),
        u"cols": str(datatype.length)}
    # Check for errors
    check_errors(context, form, datatype, name, value, schema, fields,
            readonly, attributes, tabindex=None)
    # special case for 'value'
    content = XMLContent.encode(value)
    return make_element(u"textarea", attributes, content)



def text_widget(context, form, datatype, name, value, schema, fields,
        readonly, tabindex=None):
    # Reçoit des int en GET
    if not isinstance(value, basestring):
        value = datatype.encode(value)
    if isinstance(datatype, NumDecimal):
        try:
            value = context.format_number(value, places=datatype.decimals)
        except InvalidOperation:
            pass
    # Reçoit des str en POST
    if not type(value) is unicode:
        value = unicode(value, 'utf8')
    if readonly:
        tagname = u"div"
        attributes = {u"class": [u"readonly"]}
        content = XMLContent.encode(value)
    else:
        tagname = u"input"
        attributes = {
            u"type": u"text",
            u"id": u"field_{name}".format(name=name),
            u"name": name, u"value": XMLAttribute.encode(value),
            u"size": str(datatype.size),
            u"maxlength": str(datatype.length)}
        content = u""
    # Right-align numeric fields
    if issubclass(datatype, Numeric):
        attributes.setdefault(u"class", []).append(u"num")
        attributes.setdefault(u"style", []).append(u"text-align:right")
    # Check for errors
    check_errors(context, form, datatype, name, value, schema, fields,
            readonly, attributes, tabindex=None)
    return make_element(tagname, attributes, content)



def file_widget(context, form, datatype, name, value, schema, fields,
        readonly, tabindex=None):
    if readonly:
        tagname = u"div"
        attributes = {u"class": [u"readonly"]}
        content = XMLContent.encode(value)
    else:
        tagname = u"input"
        attributes = {
            u"type": u"file",
            u"id": u"field_{name}".format(name=name),
            u"name": name, u"value": XMLAttribute.encode(value),
            u"size": str(datatype.size),
            u"maxlength": str(datatype.length)}
        content = u""
    # Check for errors
    check_errors(context, form, datatype, name, value, schema, fields,
            readonly, attributes, tabindex=None)
    html = make_element(tagname, attributes, content)
    # Preview
    if not value:
        return html
    resource = form.parent.get_resource(value, soft=True)
    if resource is None:
        return html
    context = get_context()
    link = context.get_link(resource)
    href = u"{0}/;download".format(link)
    if isinstance(resource, Image):
        src = u"{0}/;thumb?width=128&amp;height=128".format(link)
    else:
        src = u"/ui/{0}".format(resource.class_icon48)
    preview = make_element(u"a", {u"href": href, u"target": u"_new"},
            make_element(u"img", {u"src": src}))
    field_id = u"field_{name}_delete".format(name=name)
    if readonly:
        delete = u""
    else:
        delete = make_element(u"input", {
            u"type": u"checkbox",
            u"id": field_id,
            u"name": u"{name}_delete".format(name=name),
            u"value": u"1"},
                make_element(u"label", {u"for": field_id}, MSG(u"Delete")))
    html = html + preview + delete
    return html



def get_input_widget(name, form, schema, fields, context, tabindex=None,
        readonly=False, skip_print=False):
    # Always take data from the handler, we store wrong values anyway
    value = form.get_form().handler.get_value(name, schema)
    datatype = schema[name]
    readonly = readonly or datatype.readonly
    widget = None
    if  isinstance(datatype, Numeric):
        widget = text_widget
    elif issubclass(datatype, FileImage):
        widget = file_widget
    elif issubclass(datatype, Text):
        widget = textarea_widget
    elif issubclass(datatype, (EnumBoolean, SqlEnumerate)):
        representation = datatype.representation
        widget = {
            'select': select_widget,
            'radio': radio_widget,
            'checkbox': checkbox_widget}.get(representation)
        if widget is None:
            raise ValueError, representation
    else:
        widget = text_widget
    html = widget(context, form, datatype, name, value, schema, fields,
            readonly, tabindex)
    if skip_print is False:
        help = datatype.help
        if not help and isinstance(datatype, (NumDate, NumTime)):
            help = MSG(u"Format {format}").gettext(format=datatype.type)
        if help:
            html = make_element(u"div", {u"title": help, u"rel": u"tooltip"},
                    html)
    return html



class Products_Widget(RadioWidget):


    template = make_stl_template("""
    <table id="${id}" class="products-widget ${css}"
      cellpadding="5" cellspacing="5">
      <tr>
        <th></th>
        <th>Title</th>
        <th>Nb users</th>
        <th>Price (Taxes included)</th>
      </tr>
      <tr stl:repeat="option options_computed">
        <td>
          <input type="radio" id="${id}-${option/name}" name="${name}"
            value="${option/name}" checked="${option/selected}" />
        </td>
        <td>
          <label for="${id}-${option/name}">${option/value}</label>
        </td>
        <td>${option/nb_users}</td>
        <td>${option/price}</td>
      </tr>
    </table>""")

    def options_computed(self):
        root = get_context().root
        options_computed = []
        for option in self.options():
            kw = option
            product = root.get_resource(kw['name'])
            kw['nb_users'] = product.get_value('nb_users')
            kw['price'] = product.get_price_with_tax(with_devise=True)
            options_computed.append(kw)
        return options_computed
