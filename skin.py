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
from itools.core import get_abspath
from itools.web import get_context

# Import from ikaaro
from ikaaro.skins import Skin as BaseSkin
from ikaaro.skins import register_skin

# Import from goodforms
from utils import is_print



class Skin(BaseSkin):


    is_backoffice_skin = False

    def get_template(self, context):
        if is_print(get_context()):
            return self.get_resource('/ui/goodforms/print.xhtml')
        return super(Skin, self).get_template(context)


    def get_styles(self, context):
        #styles = super(Skin, self).get_styles(context)
        styles = []
        styles.append('/ui/goodforms/style_base.css')
        styles.append('/ui/goodforms/style.css')
        styles.append('/ui/goodforms/fancybox/jquery.fancybox-1.3.1.css')
        return styles


    def get_scripts(self, context):
        scripts = super(Skin, self).get_scripts(context)
        scripts.append('/ui/goodforms/zeroclipboard/ZeroClipboard.js')
        scripts.append('/ui/goodforms/fancybox/jquery.fancybox-1.3.1.pack.js')
        return scripts


register_skin('goodforms', Skin(get_abspath('ui/goodforms')))
