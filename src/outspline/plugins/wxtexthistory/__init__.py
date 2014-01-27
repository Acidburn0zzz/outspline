# Outspline - A highly modular and extensible outliner.
# Copyright (C) 2011-2014 Dario Giovannetti <dev@dariogiovannetti.net>
#
# This file is part of Outspline.
#
# Outspline is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Outspline is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Outspline.  If not, see <http://www.gnu.org/licenses/>.

import wx

import texthistory

import outspline.coreaux_api as coreaux_api
import outspline.interfaces.wxgui_api as wxgui_api

config = coreaux_api.get_plugin_configuration('wxtexthistory')

areas = {}

ID_UNDO = None
mundo = None
ID_REDO = None
mredo = None


def undo_text(event):
    tab = wxgui_api.get_selected_editor()
    if tab:
        areas[tab].undo()


def redo_text(event):
    tab = wxgui_api.get_selected_editor()
    if tab:
        areas[tab].redo()


def handle_open_textctrl(kwargs):
    areas[kwargs['item']] = texthistory.WxTextHistory(
                                         wxgui_api.get_textctrl(
                                                        kwargs['filename'],
                                                        kwargs['id_']),
                                         kwargs['text'],
                                         config.get_int('max_undos'),
                                         config.get_int('min_update_interval'))


def handle_reset_menu_items(kwargs):
    # Re-enable all the actions so they are available for their accelerators
    mundo.Enable()
    mredo.Enable()


def handle_enable_textarea_menus(kwargs):
    item = kwargs['item']

    mundo.Enable(False)
    mredo.Enable(False)

    # item is None is no editor is open
    if item:
        if areas[item].can_undo():
            mundo.Enable()
        if areas[item].can_redo():
            mredo.Enable()


def main():
    global ID_UNDO, ID_REDO
    ID_UNDO = wx.NewId()
    ID_REDO = wx.NewId()

    global mundo, mredo
    mundo = wx.MenuItem(wxgui_api.get_menu_editor(), ID_UNDO,
                                '&Undo\tCTRL+z', 'Undo the previous text edit')
    mredo = wx.MenuItem(wxgui_api.get_menu_editor(), ID_REDO,
                                    '&Redo\tCTRL+y', 'Redo the next text edit')

    mundo.SetBitmap(wx.ArtProvider.GetBitmap('@undo', wx.ART_MENU))
    mredo.SetBitmap(wx.ArtProvider.GetBitmap('@redo', wx.ART_MENU))

    separator = wx.MenuItem(wxgui_api.get_menu_editor(),
                                                        kind=wx.ITEM_SEPARATOR)

    # Add in reverse order
    wxgui_api.add_menu_editor_item(separator)
    wxgui_api.add_menu_editor_item(mredo)
    wxgui_api.add_menu_editor_item(mundo)

    wxgui_api.bind_to_menu(undo_text, mundo)
    wxgui_api.bind_to_menu(redo_text, mredo)
    wxgui_api.bind_to_open_textctrl(handle_open_textctrl)
    wxgui_api.bind_to_reset_menu_items(handle_reset_menu_items)
    wxgui_api.bind_to_menu_edit_update(handle_enable_textarea_menus)
