# Outspline - A highly modular and extensible outliner.
# Copyright (C) 2011-2013 Dario Giovannetti <dev@dariogiovannetti.net>
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

import time as _time
import datetime as _datetime
import random
import wx

import outspline.extensions.organizer_basicrules_api as organizer_basicrules_api
import outspline.plugins.wxscheduler_api as wxscheduler_api

import widgets
import msgboxes

_RULE_DESC = 'Except at regular time intervals'


class Rule():
    original_values = None
    mpanel = None
    pbox = None
    slabel = None
    startw = None
    ilabel = None
    intervalw = None
    endchoicew = None
    endw = None
    inclusivew = None

    def __init__(self, parent, filename, id_, rule):
        self.original_values = self._compute_values(rule)

        self._create_widgets(parent)

        wxscheduler_api.change_rule(filename, id_, self.mpanel)

    def _create_widgets(self, parent):
        self.mpanel = wx.Panel(parent)

        self.pbox = wx.BoxSizer(wx.VERTICAL)
        self.mpanel.SetSizer(self.pbox)

        self._create_widgets_start()
        self._create_widgets_end()
        self._create_widgets_interval()
        self._create_widgets_inclusive()

        self._align_first_column()

    def _create_widgets_start(self):
        box = wx.BoxSizer(wx.HORIZONTAL)
        self.pbox.Add(box, flag=wx.BOTTOM, border=4)

        self.slabel = wx.StaticText(self.mpanel, label='Sample start date:')
        box.Add(self.slabel, flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=4)

        self.startw = widgets.DateHourCtrl(self.mpanel)
        self.startw.set_values(self.original_values['refstartY'],
                               self.original_values['refstartm'],
                               self.original_values['refstartd'],
                               self.original_values['refstartH'],
                               self.original_values['refstartM'])
        box.Add(self.startw.get_main_panel())

    def _create_widgets_end(self):
        self.endchoicew = widgets.WidgetChoiceCtrl(self.mpanel,
                                   (('End date:', self._create_end_date_widget),
                                   ('Duration:', self._create_duration_widget)),
                                             self.original_values['endtype'], 4)
        self.endchoicew.force_update()
        self.pbox.Add(self.endchoicew.get_main_panel(), flag=wx.BOTTOM,
                                                                       border=4)

    def _create_end_date_widget(self):
        self.endw = widgets.DateHourCtrl(self.endchoicew.get_main_panel())
        self.endw.set_values(self.original_values['refendY'],
                             self.original_values['refendm'],
                             self.original_values['refendd'],
                             self.original_values['refendH'],
                             self.original_values['refendM'])

        return self.endw.get_main_panel()

    def _create_duration_widget(self):
        self.endw = widgets.TimeSpanCtrl(self.endchoicew.get_main_panel(), 1)
        self.endw.set_values(self.original_values['rendn'],
                             self.original_values['rendu'])

        return self.endw.get_main_panel()

    def _create_widgets_interval(self):
        box = wx.BoxSizer(wx.HORIZONTAL)
        self.pbox.Add(box, flag=wx.BOTTOM, border=4)

        self.ilabel = wx.StaticText(self.mpanel, label='Interval time:')
        box.Add(self.ilabel, flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=4)

        self.intervalw = widgets.TimeSpanCtrl(self.mpanel, 1)
        self.intervalw.set_values(self.original_values['intervaln'],
                                  self.original_values['intervalu'])
        box.Add(self.intervalw.get_main_panel())

    def _create_widgets_inclusive(self):
        box = wx.BoxSizer(wx.HORIZONTAL)
        self.pbox.Add(box)

        self.inclusivew = wx.CheckBox(self.mpanel)
        self.inclusivew.SetValue(self.original_values['inclusive'])
        box.Add(self.inclusivew)

        ilabel = wx.StaticText(self.mpanel, label='Inclusive')
        box.Add(ilabel, flag=wx.ALIGN_CENTER_VERTICAL)

    def _align_first_column(self):
        sminw = self.slabel.GetSizeTuple()[0]
        eminw = self.endchoicew.get_choice_width()
        iminw = self.ilabel.GetSizeTuple()[0]

        maxw = max((sminw, eminw, iminw))

        sminh = self.slabel.GetMinHeight()
        self.slabel.SetMinSize((maxw, sminh))

        self.endchoicew.set_choice_min_width(maxw)

        iminh = self.ilabel.GetMinHeight()
        self.ilabel.SetMinSize((maxw, iminh))

    def apply_rule(self, filename, id_):
        refstart = self.startw.get_unix_time()

        endtype = self.endchoicew.get_selection()

        if endtype == 1:
            rend = self.endw.get_time_span()
            rendn = self.endw.get_number()
            rendu = self.endw.get_unit()
        else:
            rend = self.endw.get_unix_time() - refstart
            rendn = None
            rendu = None

        interval = self.intervalw.get_time_span()
        intervaln = self.intervalw.get_number()
        intervalu = self.intervalw.get_unit()

        inclusive = self.inclusivew.GetValue()

        try:
            ruled = organizer_basicrules_api.make_except_regularly_single_rule(
                               refstart, interval, rend, inclusive, (endtype, ))
        except organizer_basicrules_api.BadRuleError:
            msgboxes.warn_bad_rule().ShowModal()
        else:
            label = self._make_label(intervaln, intervalu, refstart, rend,
                                               inclusive, endtype, rendn, rendu)
            wxscheduler_api.apply_rule(filename, id_, ruled, label)

    @classmethod
    def insert_rule(cls, filename, id_, rule, rulev):
        values = cls._compute_values(rulev)
        label = cls._make_label(values['intervaln'], values['intervalu'],
                        values['refstart'], values['rend'], values['inclusive'],
                            values['endtype'], values['rendn'], values['rendu'])
        wxscheduler_api.insert_rule(filename, id_, rule, label)

    @classmethod
    def _compute_values(cls, rule):
        values = {}

        if not rule:
            values['refstart'] = (int(_time.time()) // 3600 + 1) * 3600
            values['refmax'] = values['refstart'] + 3600

            values.update({
                'refspan': values['refmax'] - values['refstart'],
                'interval': 86400,
                'rend': 3600,
                'inclusive': False,
                'endtype': 0,
            })
        else:
            values = {
                'refmax': rule[0],
                'refspan': rule[1],
                'interval': rule[2],
                'rend': rule[3] if rule[3] is not None else 3600,
                'inclusive': rule[4],
                'endtype': rule[5][0],
            }

            values['refstart'] = values['refmax'] - values['refspan']

        values['intervaln'], values['intervalu'] = \
                 widgets.TimeSpanCtrl._compute_widget_values(values['interval'])

        values['rendn'], values['rendu'] = \
                     widgets.TimeSpanCtrl._compute_widget_values(values['rend'])

        localstart = _datetime.datetime.fromtimestamp(values['refstart'])
        localend = _datetime.datetime.fromtimestamp(values['refstart'] +
                                                                 values['rend'])

        values.update({
            'refstartY': localstart.year,
            'refstartm': localstart.month - 1,
            'refstartd': localstart.day,
            'refstartH': localstart.hour,
            'refstartM': localstart.minute,
            'refendY': localend.year,
            'refendm': localend.month - 1,
            'refendd': localend.day,
            'refendH': localend.hour,
            'refendM': localend.minute,
        })

        return values

    @staticmethod
    def _make_label(intervaln, intervalu, refstart, rend, inclusive, endtype,
                                                                  rendn, rendu):
        label = 'Except every {} {}'.format(intervaln, intervalu)

        label += ', for example on {}'.format(_time.strftime(
                             '%a %d %b %Y at %H:%M', _time.localtime(refstart)))

        if endtype == 1:
            label += ' for {} {}'.format(rendn, rendu)
        else:
            label += _time.strftime(' until %a %d %b %Y at %H:%M',
                                               _time.localtime(refstart + rend))

        if inclusive:
            label += ', inclusive'

        return label

    @staticmethod
    def create_random_rule():
        refstart = int((random.gauss(_time.time(), 15000)) // 60 * 60)

        interval = random.randint(1, 4320) * 60

        endtype = random.choice((0, 1))

        rend = random.randint(1, 360) * 60

        inclusive = random.choice((True, False))

        return organizer_basicrules_api.make_except_regularly_single_rule(
                               refstart, interval, rend, inclusive, (endtype, ))
