# -*- coding: UTF-8 -*-
# Copyright (C) 2009-2010 Hervé Cauwelier <herve@itaapy.com>
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
from itools.datatypes import Enumerate
from itools.gettext import MSG
from itools.workflow import Workflow


# States
NOT_REGISTERED = 'not_registered'
EMPTY = 'private'
PENDING = 'pending'
FINISHED = 'public'
EXPORTED = 'exported'
MODIFIED = 'modified'


class WorkflowState(Enumerate):
    options = [
        {'name': NOT_REGISTERED, 'value': MSG(u"Not Registered")},
        {'name': EMPTY, 'value': MSG(u"Empty")},
        {'name': PENDING, 'value': MSG(u"Pending")},
        {'name': FINISHED, 'value': MSG(u"Finished")},
        #{'name': EXPORTED, 'value': MSG(u"Exported")},
        #{'name': MODIFIED, 'value': MSG(u"Modified after export")},
    ]



workflow = Workflow()
for option in WorkflowState.get_options():
    workflow.add_state(option['name'], title=option['value'])
workflow.set_initstate(EMPTY)
