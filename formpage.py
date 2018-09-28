# -*- coding: UTF-8 -*-
# Copyright (C) 2005  <jdavid@favela.(none)>
# Copyright (C) 2006 J. David Ibanez <jdavid@itaapy.com>
# Copyright (C) 2006 luis <luis@lucifer.localdomain>
# Copyright (C) 2006-2008, 2010 Hervé Cauwelier <herve@itaapy.com>
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
from csv import reader as read_csv

# Import from itools
from itools.core import freeze
from itools.csv import CSVFile, parse
from itools.datatypes import XMLAttribute, Unicode
from itools.gettext import MSG
from itools.handlers import guess_encoding
from itools.web import ERROR
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro.folder import Folder
from ikaaro.fields import Char_Field, File_Field

# Import from goodforms
from datatypes import NumTime
from schema import Variable
from utils import FormatError
from widgets import get_input_widget, make_element
from workflow import FINISHED, EXPORTED


NBSP = u"\u00a0".encode('utf8')
FIELD_PREFIX = u"#"
ERR_BAD_NAME = ERROR(u'In "{title}" sheet, line {line}, variable "{name}" is unknown.')


def is_disabled(row):
    is_disabled = False
    for column in row:
        if u"disabled" in column['class']:
            is_disabled = True
        elif u"field-widget" in column['class']:
            return False
    return is_disabled



class FormPageHandler(CSVFile):

    schema = freeze({'null': Unicode})
    columns = ['null']


#    def _load_state_from_file(self, file, encoding='UTF-8'):
#        # Read the data, and find out the encoding
#        data = file.read()
#        self.encoding = guess_encoding(data)
#
#        # Sniff number of columns
#        lines = data.splitlines(True)
#        reader = read_csv(lines)
#        line = reader.next()
#        self.columns = columns = ['null'] * len(line)
#
#        for line in parse(data, columns, self.schema,
#                guess=self.class_csv_guess, skip_header=self.skip_header,
#                encoding=self.encoding):
#            self._add_row(line)
#
#
#    def to_str(self, encoding='UTF-8', separator=',', newline='\n'):
#        # FIXME WHY ?
#        lines = []
#        for row in self.get_rows():
#            line = []
#            for value in row:
#                data = Unicode.encode(value, encoding=encoding)
#                line.append('"%s"' % data.replace('"', '""'))
#            lines.append(separator.join(line))
#        return newline.join(lines)



class FormPage(Folder):

    class_id = 'FormPage'
    class_title = MSG(u"Form Page")
    class_views = ['edit']

    # Fields
    data = File_Field(class_handler=FormPageHandler)
    filename = Char_Field
    extension = Char_Field

    def _load_from_csv(self):
        handler = self.get_value('data')
        title = self.get_title()
        handler.load_state_from_string(body)
        schema_resource = self.parent.get_resource('schema')
        schema, pages = schema_resource.get_schema_pages()
        # Consistency check
        for lineno, row in enumerate(handler.get_rows()):
            lineno += 1
            for column in row:
                if column.startswith(Variable.FIELD_PREFIX):
                    name = Variable.decode(column)
                    if name and name not in schema:
                        raise FormatError, ERR_BAD_NAME(title=title,
                                line=lineno, name=name)


    def get_page_number(self):
        # Let error raise
        _, page_number = self.name.split('page')
        return page_number.upper()


    def get_page_fields(self):
        handler = self.get_value('data')
        for row in handler.get_rows():
            for column in row:
                column = column.strip()
                if column.startswith(FIELD_PREFIX):
                    column = column[1:]
                    if column:
                        yield str(column)


    def get_namespace(self, form, view, context, skip_print=False,
            readonly=False):
        # Force l'ordre de tabulation entre les champs
        tabindex = 0
        page_number = self.get_page_number()

        # Lecture seule ?
        root = self.get_resource('/')
        if not skip_print and not root.is_allowed_to_edit(context.user, form):
            state = form.get_workflow_state()
            if state in (FINISHED, EXPORTED):
                readonly = True
        # 0005160: affiche les champs même en lecture seule
        elif skip_print:
            readonly = True

        schema = form.get_schema()
        fields = form.get_form_fields(schema)
        globals_ = form.get_globals()
        locals_ = form.get_locals(schema, fields)
        floating_locals = form.get_floating_locals(schema, fields)

        # Calcul du (des) tableau(x)
        tables = []
        tables.append([])
        handler = self.get_value('data')
        for y, row in enumerate(handler.get_rows()):
            columns = []
            for x, column in enumerate(row):
                tabindex = str(x * 100 + y + 1)
                column = column.strip()
                if column == u"-":
                    # Espace blanc insécable
                    try:
                        css_class = columns[-1]['class']
                    except IndexError:
                        css_class = u"field-label"
                    columns.append({
                        'rowspan': None,
                        'colspan': None,
                        'body': XMLParser(NBSP),
                        'class': css_class})
                elif column == u"%break%":
                    # Saut de page
                    columns.append({
                        'rowspan': None,
                        'colspan': None,
                        'body': XMLParser(NBSP),
                        'class': u""})
                    # Commence un nouveau tableau
                    tables.append([])
                elif column.startswith(FIELD_PREFIX):
                    # Champ à remplacer par un widget
                    css_class = u"field-widget"
                    column = column[1:]
                    if not column:
                        # Un « # » seul pour préfixer les champs
                        # Fusionne avec la cellule précédente (svt un titre)
                        colspan = (columns[-1]['colspan'] or 1) + 1
                        columns[-1]['colspan'] = colspan
                        continue
                    elif str(column) in schema:
                        datatype = schema[column]
                        if form.is_disabled_by_type(column, schema,
                                datatype):
                            column = u""
                            css_class = u"disabled"
                        else:
                            column = get_input_widget(column, form, schema,
                                    fields, context, tabindex=tabindex,
                                    readonly=readonly, skip_print=skip_print)
                    else:
                        # 0004922 Fiche école ne fonctionne plus
                        column = column.replace(u'\n', u'')
                        try:
                            if u"/" in column:
                                column = eval(column, globals_,
                                        floating_locals)
                            else:
                                column = eval(column, globals_, locals_)
                        except ZeroDivisionError:
                            column = MSG(u"(division by 0)")
                        except SyntaxError:
                            raise SyntaxError, repr(column)
                    if not isinstance(column, basestring):
                        css_class += u" num"
                        if isinstance(column, NumTime):
                            # 0006611 numérique mais représentation textuelle
                            column = unicode(column)
                        elif type(column) is int:
                            # l'opération était préfixée par int
                            column = u"%d" % column
                        elif str(column) != 'NC':
                            column = u"%.1f" % column
                        else:
                            column = unicode(column)
                    body = XMLParser(column.encode('utf8'))
                    columns.append({
                        'rowspan': None,
                        'colspan': None,
                        'body': body,
                        'class': css_class})
                elif column:
                    column = XMLAttribute.encode(column)
                    # Texte simple (ou pas)
                    if column[0] == u"*":
                        # 0007975: Gestion des titres
                        new_column = column.lstrip(u"*")
                        level = len(column) - len(new_column)
                        column = new_column.strip()
                        column = make_element(
                                # <h1> est déjà pris
                                u"h%d" % (int(level) + 1),
                                content=column.strip())
                        css_class = u"section-header"
                        # Commence un nouveau tableau
                        tables.append([])
                    elif (  # 0007970: CSS spécifique pour numéros de
                            # rubriques
                            column in schema
                            # 0008569: BDP : les numéros de rubrique ne sont
                            # pas tous de la même taille
                            or x + 1 == len(row)):
                        css_class = u"rubrique-label"
                    else:
                        css_class = u"field-label"
                    if column == u"100%":
                        css_class += u" num"
                    body = XMLParser(column.encode('utf8'))
                    columns.append({
                        'rowspan': None,
                        'colspan': None,
                        'body': body,
                        'class': css_class})
                elif columns:
                    # Vide : fusionne avec la précédente
                    colspan = (columns[-1]['colspan'] or 1) + 1
                    columns[-1]['colspan'] = colspan
                    continue
                else:
                    # Ligne vraiment vide
                    columns.append({
                        'rowspan': None,
                        'colspan': None,
                        'body': '',
                        'class': u"empty"})
            # Filtre les lignes vides
            if is_disabled(columns):
                tables[-1].append([{
                    'rowspan': None,
                    'colspan': len(row),
                    'body': '',
                    'class': u"removed"}])
            else:
                tables[-1].append(columns)

        # Filtre en-têtes vides
        for i, table in reversed(list(enumerate(tables))):
            label_without_widget =  False
            for j, row in reversed(list(enumerate(table))):
                for column in row:
                    css_class = column['class']
                    if u"field-widget" in css_class:
                        break
                    elif u"field-label" in css_class:
                        label_without_widget = True
                else:
                    if label_without_widget is True:
                        del table[j]
                    continue
                break
            else:
                if label_without_widget is True:
                    del tables[i]

        # Filtre titres vides
        for i, table in reversed(list(enumerate(tables))):
            has_title = False
            has_removed = False
            for j, row in reversed(list(enumerate(table))):
                for column in row:
                    css_class = column['class']
                    if u"field-widget" in css_class:
                        break
                    elif u"section-header" in css_class:
                        has_title = True
                    elif u"removed" in css_class:
                        has_removed = True
                else:
                    continue
                break
            else:
                if has_title and has_removed:
                    del tables[i]

        # Filtre lignes supprimées
        for i, table in reversed(list(enumerate(tables))):
            for j, row in reversed(list(enumerate(table))):
                for column in row:
                    css_class = column['class']
                    if u"removed" in css_class:
                        del table[j]
                        break

        namespace = {}
        namespace['form_title'] = form.get_title()
        namespace['page_title'] = view.get_title(context)
        namespace['page_number'] = page_number
        namespace['tables'] = tables
        namespace['readonly'] = skip_print or readonly
        namespace['first_time'] = form.is_first_time()
        namespace['skip_print'] = skip_print
        return namespace
