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

import time as _time
import datetime as _datetime
import random
import wx

import organism.extensions.organizer_basicrules_api as organizer_basicrules_api
import organism.plugins.wxscheduler_api as wxscheduler_api

import widgets
import msgboxes

_RULE_DESC = 'Occur every n years'


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
    alarmchoicew = None
    alarmw = None

    def __init__(self, parent, filename, id_, rule):
        self.original_values = self._compute_values(rule)

        self._create_widgets(parent)

        wxscheduler_api.change_rule(filename, id_, self.mpanel)

    def _create_widgets(self, parent):
        self.mpanel = wx.Panel(parent)

        self.pbox = wx.BoxSizer(wx.VERTICAL)
        self.mpanel.SetSizer(self.pbox)

        self._create_widgets_start()
        self._create_widgets_interval()
        self._create_widgets_end()
        self._create_widgets_alarm()

        self._align_first_column()

    def _create_widgets_start(self):
        box = wx.BoxSizer(wx.HORIZONTAL)
        self.pbox.Add(box, flag=wx.BOTTOM, border=4)

        self.slabel = wx.StaticText(self.mpanel, label='Sample start date:')
        box.Add(self.slabel, flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=4)

        self.startw = widgets.DateHourCtrl(self.mpanel)
        self.startw.set_values(self.original_values['refyear'],
                               self.original_values['mmonth'],
                               self.original_values['day'],
                               self.original_values['rstartH'],
                               self.original_values['rstartM'])
        box.Add(self.startw.get_main_panel())

    def _create_widgets_interval(self):
        box = wx.BoxSizer(wx.HORIZONTAL)
        self.pbox.Add(box, flag=wx.BOTTOM, border=4)

        self.ilabel = wx.StaticText(self.mpanel, label='Interval (years):')
        box.Add(self.ilabel, flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=4)

        self.intervalw = wx.SpinCtrl(self.mpanel, min=1, max=99, size=(48, 21),
                                                         style=wx.SP_ARROW_KEYS)
        self.intervalw.SetValue(self.original_values['interval'])
        box.Add(self.intervalw, flag=wx.ALIGN_CENTER_VERTICAL)

    def _create_widgets_end(self):
        self.endchoicew = widgets.WidgetChoiceCtrl(self.mpanel,
                                                         (('No duration', None),
                                    ('Duration:', self._create_duration_widget),
                                   ('End time:', self._create_end_time_widget)),
                                             self.original_values['endtype'], 4)
        self.endchoicew.force_update()
        self.pbox.Add(self.endchoicew.get_main_panel(), flag=wx.BOTTOM,
                                                                       border=4)

    def _create_duration_widget(self):
        self.endw = widgets.TimeSpanCtrl(self.endchoicew.get_main_panel(), 1)
        self.endw.set_values(self.original_values['rendn'],
                             self.original_values['rendu'])

        return self.endw.get_main_panel()

    def _create_end_time_widget(self):
        self.endw = widgets.HourCtrl(self.endchoicew.get_main_panel())
        self.endw.set_values(self.original_values['rendH'],
                             self.original_values['rendM'])

        return self.endw.get_main_panel()

    def _create_widgets_alarm(self):
        self.alarmchoicew = widgets.WidgetChoiceCtrl(self.mpanel,
                                                            (('No alarm', None),
                          ('Alarm advance:', self._create_alarm_advance_widget),
                               ('Alarm time:', self._create_alarm_time_widget)),
                                           self.original_values['alarmtype'], 4)
        self.alarmchoicew.force_update()
        self.pbox.Add(self.alarmchoicew.get_main_panel())

    def _create_alarm_advance_widget(self):
        self.alarmw = widgets.TimeSpanCtrl(self.alarmchoicew.get_main_panel(),
                                                                              0)
        self.alarmw.set_values(self.original_values['ralarmn'],
                               self.original_values['ralarmu'])

        return self.alarmw.get_main_panel()

    def _create_alarm_time_widget(self):
        self.alarmw = widgets.HourCtrl(self.alarmchoicew.get_main_panel())
        self.alarmw.set_values(self.original_values['ralarmH'],
                               self.original_values['ralarmM'])

        return self.alarmw.get_main_panel()

    def _align_first_column(self):
        sminw = self.slabel.GetSizeTuple()[0]
        iminw = self.ilabel.GetSizeTuple()[0]
        eminw = self.endchoicew.get_choice_width()
        aminw = self.alarmchoicew.get_choice_width()

        maxw = max((sminw, iminw, eminw, aminw))

        sminh = self.slabel.GetMinHeight()
        self.slabel.SetMinSize((maxw, sminh))

        iminh = self.ilabel.GetMinHeight()
        self.ilabel.SetMinSize((maxw, iminh))

        self.endchoicew.set_choice_min_width(maxw)

        self.alarmchoicew.set_choice_min_width(maxw)

    def apply_rule(self, filename, id_):
        refstart = self.startw.get_unix_time()
        refyear = self.startw.get_year()
        month = self.startw.get_month() + 1
        day = self.startw.get_day()
        rstart = (refstart - _time.altzone) % 86400

        interval = self.intervalw.GetValue()

        endtype = self.endchoicew.get_selection()

        if endtype == 1:
            rend = self.endw.get_time_span()
            fend = False
            rendn = self.endw.get_number()
            rendu = self.endw.get_unit()
            rendH = None
            rendM = None
        elif endtype == 2:
            endrt = self.endw.get_relative_time()

            # If time is set earlier than or equal to start, interpret it as
            # referring to the following day
            if endrt > rstart:
                rend = endrt - rstart
                fend = False
            else:
                rend = 86400 - rstart + endrt
                fend = True

            rendn = None
            rendu = None
            rendH = self.endw.get_hour()
            rendM = self.endw.get_minute()
        else:
            rend = None
            fend = False
            rendn = None
            rendu = None
            rendH = None
            rendM = None

        alarmtype = self.alarmchoicew.get_selection()

        if alarmtype == 1:
            ralarm = self.alarmw.get_time_span()
            palarm = False
            ralarmn = self.alarmw.get_number()
            ralarmu = self.alarmw.get_unit()
            ralarmH = None
            ralarmM = None
        elif alarmtype == 2:
            alarmrt = self.alarmw.get_relative_time()

            # If time is set later than start, interpret it as referring to
            # the previous day
            if alarmrt <= rstart:
                ralarm = rstart - alarmrt
                palarm = False
            else:
                ralarm = 86400 - alarmrt + rstart
                palarm = True

            ralarmn = None
            ralarmu = None
            ralarmH = self.alarmw.get_hour()
            ralarmM = self.alarmw.get_minute()
        else:
            ralarm = None
            palarm = False
            ralarmn = None
            ralarmu = None
            ralarmH = None
            ralarmM = None

        try:
            ruled = organizer_basicrules_api.make_occur_yearly_single_rule(
                            interval, refyear, month, day, rstart, rend, ralarm,
                                                           (endtype, alarmtype))
        except organizer_basicrules_api.BadRuleError:
            msgboxes.warn_bad_rule().ShowModal()
        else:
            label = self._make_label(interval, refyear, month, day, rstart,
                                   rendH, rendM, ralarmH, ralarmM, rendn, rendu,
                             ralarmn, ralarmu, endtype, alarmtype, fend, palarm)
            wxscheduler_api.apply_rule(filename, id_, ruled, label)

    @classmethod
    def insert_rule(cls, filename, id_, rule, rulev):
        values = cls._compute_values(rulev)
        label = cls._make_label(values['interval'], values['refyear'],
                               values['month'], values['day'], values['rstart'],
                            values['rendH'], values['rendM'], values['ralarmH'],
                            values['ralarmM'], values['rendn'], values['rendu'],
                        values['ralarmn'], values['ralarmu'], values['endtype'],
                          values['alarmtype'], values['fend'], values['palarm'])
        wxscheduler_api.insert_rule(filename, id_, rule, label)

    @classmethod
    def _compute_values(cls, rule):
        values = {}

        if not rule:
            nh = (int(_time.time()) // 3600 + 1) * 3600
            sdate = _datetime.datetime.fromtimestamp(nh)

            values.update({
                'interval': 1,
                'refyear': sdate.year,
                'month': sdate.month,
                'day':sdate.day,
                'rstart': sdate.hour * 3600,
                'rend': 3600,
                'ralarm': 0,
                'endtype': 0,
                'alarmtype': 0,
            })
        else:
            values = {
                'maxoverlap': rule[0],
                'interval': rule[1],
                'refyear': rule[2],
                'month': rule[3],
                'day': rule[4],
                'rstart': rule[5],
                'rend': rule[6] if rule[6] is not None else 3600,
                'ralarm': rule[7] if rule[7] is not None else 0,
                'endtype': rule[8][0],
                'alarmtype': rule[8][1],
            }

            sdate = _datetime.datetime(values['refyear'], values['month'],
                  values['day']) + _datetime.timedelta(seconds=values['rstart'])

        values['rendn'], values['rendu'] = \
                     widgets.TimeSpanCtrl._compute_widget_values(values['rend'])

        # ralarm could be negative
        values['ralarmn'], values['ralarmu'] = \
                                    widgets.TimeSpanCtrl._compute_widget_values(
                                                     max((0, values['ralarm'])))

        rrend = values['rstart'] + values['rend']
        values['fend'] = False

        # End time could be set after 23:59 of the start day
        if rrend > 86399:
            rrend = rrend % 86400
            values['fend'] = True

        rralarm = values['rstart'] - values['ralarm']
        values['palarm'] = False

        # Alarm time could be set before 00:00 of the start day
        if rralarm < 0:
            rralarm = 86400 - abs(rralarm) % 86400
            values['palarm'] = True

        values.update({
            'mmonth': values['month'] - 1,
            'rstartH': values['rstart'] // 3600,
            'rstartM': values['rstart'] % 3600 // 60,
            'rendH': rrend // 3600,
            'rendM': rrend % 3600 // 60,
            'ralarmH': rralarm // 3600,
            'ralarmM': rralarm % 3600 // 60,
        })

        return values

    @staticmethod
    def _make_label(interval, refyear, month, day, rstart,
                                   rendH, rendM, ralarmH, ralarmM, rendn, rendu,
                            ralarmn, ralarmu, endtype, alarmtype, fend, palarm):
        label = 'Occur on {} {} at {}:{} every {} years (e.g. {})'.format(day,
                               widgets.DateHourCtrl._compute_month_label(month),
                str(rstart // 3600).zfill(2), str(rstart % 3600 // 60).zfill(2),
                                                              interval, refyear)

        if endtype == 1:
            label += ' for {} {}'.format(rendn, rendu)
        elif endtype == 2:
            label += ' until {}:{}'.format(str(rendH).zfill(2),
                                                            str(rendM).zfill(2))
            if fend:
                label += ' of the following day'

        if alarmtype == 1:
            label += ', activate alarm {} {} before'.format(ralarmn, ralarmu)
        elif alarmtype == 2:
            label += ', activate alarm at {}:{}'.format(
                                   str(ralarmH).zfill(2), str(ralarmM).zfill(2))
            if palarm:
                label += ' of the previous day'

        return label

    @staticmethod
    def create_random_rule():
        interval = random.randint(1, 3)
        refyear = random.randint(1990, 2020)
        month = random.randint(1, 12)

        while True:
            day = random.randint(1, 31)

            try:
                _datetime.date(refyear, month, day)
            except ValueError:
                continue
            else:
                break

        rstart = random.randint(0, 1440) * 60

        endtype = random.randint(0, 2)

        if endtype == 0:
            rend = None
        else:
            rend = random.randint(1, 360) * 60

        alarmtype = random.randint(0, 2)

        if alarmtype == 0:
            ralarm = None
        else:
            ralarm = random.randint(0, 360) * 60

        return organizer_basicrules_api.make_occur_yearly_single_rule(interval,
                refyear, month, day, rstart, rend, ralarm, (endtype, alarmtype))