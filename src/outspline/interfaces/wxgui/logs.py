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

import outspline.core_api as core_api
import outspline.coreaux_api as coreaux_api


class LogsConfiguration(object):
    def __init__(self):
        config = coreaux_api.get_interface_configuration('wxgui')

        # Use a copy of the original constant, so that every time a database is
        # opened it reads the current value, and not the one stored in the
        # configuration
        # Do not put this into the DatabaseHistory class, since it must be a
        # database-independent value
        self.show_status = config.get_bool('show_logs')

    def is_shown(self):
        return self.show_status

    def set_shown(self, flag=True):
        self.show_status = flag


class DatabaseHistory(object):
    def __init__(self, parent, filename):
        self.filename = filename
        self.config = coreaux_api.get_interface_configuration('wxgui')
        bgcolor = parent.treec.GetBackgroundColour()

        self.scwindow = wx.ScrolledWindow(parent, style=wx.BORDER_THEME)
        self.scwindow.SetScrollRate(20, 20)
        self.scwindow.SetBackgroundColour(bgcolor)

        self.grid = wx.FlexGridSizer(cols=2, hgap=4)
        self.grid.AddGrowableCol(1, 1)
        self.scwindow.SetSizer(self.grid)

        self._set_colors(bgcolor)

        if self.config.get_bool('debug_history'):
            self.format_action = lambda row: "".join(("[",
                            str(row['H_status']), "] ", row['H_description']))
        else:
            self.format_action = lambda row: row['H_description']

        self.cmenu = ContextMenu(filename)

        self.scwindow.Bind(wx.EVT_CONTEXT_MENU, self._popup_context_menu)

        self.refresh()

    def _set_colors(self, bgcolor):
        coldone = self.config['history_color_done']
        colundone = self.config['history_color_undone']
        colsaved = self.config['history_color_saved']

        if coldone == 'none':
            colordone = bgcolor
        else:
            colordone = wx.Colour()
            colordone.SetFromString(coldone)

        if colundone == 'none':
            colorundone = bgcolor
        else:
            colorundone = wx.Colour()
            colorundone.SetFromString(colundone)

        if colsaved == 'none':
            colorsaved = bgcolor
        else:
            colorsaved = wx.Colour()
            colorsaved.SetFromString(colsaved)

        self.colors = {
            0: colorundone,
            1: colordone,
            2: colorundone,
            3: colordone,
            4: colorundone,
            5: colorsaved,
        }

    def refresh(self):
        # Don't use self.scwindow.DestroyChildren() because it wouldn't also
        # delete the spacer; moreover, while refreshing, all the StaticText
        # items would appear all overlapping until the Layout, which doesn't
        # happen with self.box.Clear(True)
        self.grid.Clear(True)

        self.grid.AddSpacer(4)
        self.grid.AddSpacer(4)

        descriptions = core_api.get_history_descriptions(self.filename)

        for row in descriptions:
            text = wx.StaticText(self.scwindow, label=self.format_action(row))
            status = wx.Panel(self.scwindow,
                                        size=(6, text.GetSize().GetHeight()))
            status.SetBackgroundColour(self.colors[row['H_status']])

            self.grid.Add(status)
            self.grid.Add(text)

        self.scwindow.Layout()

    def _popup_context_menu(self, event):
        self.cmenu.update_items()
        self.scwindow.PopupMenu(self.cmenu)


class ContextMenu(wx.Menu):
    def __init__(self, filename):
        wx.Menu.__init__(self)
        self.filename = filename

        self.hide = wx.MenuItem(self, wx.GetApp().menu.view.ID_LOGS,
                                                                "&Hide logs")
        self.undo = wx.MenuItem(self, wx.GetApp().menu.database.ID_UNDO,
                                                                    "&Undo")
        self.redo = wx.MenuItem(self, wx.GetApp().menu.database.ID_REDO,
                                                                    "&Redo")

        self.hide.SetBitmap(wx.ArtProvider.GetBitmap('@logs', wx.ART_MENU))
        self.undo.SetBitmap(wx.ArtProvider.GetBitmap('@undo', wx.ART_MENU))
        self.redo.SetBitmap(wx.ArtProvider.GetBitmap('@redo', wx.ART_MENU))

        self.AppendItem(self.hide)
        self.AppendSeparator()
        self.AppendItem(self.undo)
        self.AppendItem(self.redo)

    def _reset_items(self):
        self.undo.Enable(False)
        self.redo.Enable(False)

    def update_items(self):
        self._reset_items()

        if core_api.preview_undo_tree(self.filename):
            self.undo.Enable()

        if core_api.preview_redo_tree(self.filename):
            self.redo.Enable()