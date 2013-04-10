# Organism - A highly modular and extensible outliner.
# Copyright (C) 2011-2013 Dario Giovannetti <dev@dariogiovannetti.net>
#
# This file is part of Organism.
#
# Organism is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Organism is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Organism.  If not, see <http://www.gnu.org/licenses/>.

import wx

import organism.coreaux_api as coreaux_api
import organism.interfaces.wxgui_api as wxgui_api


def main():
    config = coreaux_api.get_plugin_configuration('wxpreferences')
    ID_PREFERENCES = wx.NewId()
    wxgui_api.insert_menu_item('View', config.get_int('menu_pos'),
                               '&Preferences', id_=ID_PREFERENCES,
                               help='Open preferences',
                               sep=config['menu_sep'],
                               icon='@preferences').Enable(False)
