#!/usr/bin/env python

import sys
import json
import re
import string

doc_height = 400
doc_margin = 20
start_x = 50
conf_file = 'roadmap.json'

months = ['january', 'february', 'march', 'april', 'may', 'june', 'july',
          'august', 'september', 'october', 'november', 'december']

def mno_from_mo(mo):
    if not mo:
        return None
    mo = string.split(mo)[0]
    z = re.compile('^%s' % mo, re.I)
    for x in range(0, len(months)):
        if z.match(months[x]):
            return x + 1
    return None

def yno_from_mo(mo):
    if not mo:
        return None
    yr = string.split(mo)[1]
    return int(yr)

class Month(object):
    def __init__(self, yr, mo):
        self.yr = int(yr)
        self.mo = int(mo)

    def months_tuple(self, c):
        yr = self.yr
        mo = self.mo
        while c > 0:
            mo += 1
            if mo == 13:
                yr += 1
                mo = 1
            c -= 1
        return (yr, mo)

    def __add__(self, no):
        (yr, mo) = self.months_tuple(no)
        return Month(yr, mo)

    def __iadd__(self, no):
        (yr, mo) = self.months_tuple(no)
        self.yr = yr
        self.mo = mo
        return self

    def __eq__(self, t):
        return self.yr == t[0] and self.mo == t[1]

    def __ne__(self, t):
        return not self == t

    def __str__(self):
        return "{%s, %s}" % (self.yr, self.mo)

class GraphInfo(object):
    def __init__(self):
        self.ms_per_mo = None
        self.months = []
        self.bottom = 0

def calc_graph_info(divs):
    gi = GraphInfo()

    e_year = 9999
    l_year = 0

    # Find first and last year
    for d in divs:
        for ms in d.mss:
            if ms.yno < e_year:
                e_year = ms.yno
            if ms.yno > l_year:
                l_year = ms.yno

    # Find first and last months and the counts per month
    e_month = 13
    l_month = 0
    m = []
    for d in divs:
        for ms in d.mss:
            c = {}
            if ms.yno == e_year and ms.mno < e_month:
                e_month = ms.mno
            if ms.yno == l_year and ms.mno > l_month:
                l_month = ms.mno
            c[(ms.yno, ms.mno)] = c.get((ms.yno, ms.mno), 0) + 1
            m.append(max(c.values()))

    gi.ms_per_mo = max(m)

    z = Month(e_year, e_month)
    while z != (l_year, l_month):
        gi.months.append(z)
        z = z + 1
    gi.months.append(z)

    for m in gi.months:
        print >> sys.stderr, m

    return gi

class Drawing(object):
    def __init__(self):
        pass

    def set_color(self, c):
        self.color = c

    def line(self, x1, y1, x2, y2, lw):
        pass

    def text(self, s, x, y, bold=False, pix=0):
        pass

    def text_pixlen(self, s):
        return 0

    def circle(self, x, y, r, sw):
        pass

    def create(self):
        pass

    def close(self):
        pass

class SVG(Drawing):
    pix_per_char = 12
    grid_spaces = 21

    def __init__(self):
        super(SVG, self).__init__()

    def text(self, s, x, y, bold=False, pix=pix_per_char):
        weight = ""
        if bold:
            weight = "font-weight: bold;"
        style = "font-family:monospace;font-size:%dpx;%s" % (pix, weight)
        print '<text style="%s" x="%d" y="%d" fill="%s">%s</text>' %\
            (style, x, y, self.color, s)

    def text_pixlen(self, s, pix=pix_per_char):
        if not s:
            return 0
        return len(s) * (pix * (float(2)/float(3)))

    def grid(self, x, y):
        self.set_color("grey")
        at = 0
        while at < x:
            self.line(at, 0, at, y)
            at += SVG.grid_spaces
        at = 0
        while at < y:
            self.line(0, at, x, at)
            at += SVG.grid_spaces

    def create(self, x, y):
        print '<?xml version="1.0" encoding="UTF-8" standalone="no"?>'
        print '<svg width="%d" height="%d" xmlns="http://www.w3.org/2000/svg">' % (x, y)

        self.grid(x, y)
        self.width = x
        self.height = y

    def circle(self, x, y, r, sw):
        print '<circle cx="%d" cy="%d" r="%d" stroke="%s" stroke-width="%d" fill="white" />' %\
            (x, y, r, self.color, sw)

    def line(self, x1, y1, x2, y2, lw=1):
        print '<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="%d" />' %\
            (x1, y1, x2, y2, self.color, lw)

    def close(self):
        print '</svg>'

class Division(object):
    pix_per_name = 18

    def __init__(self, name, color):
        self.name = name
        self.color = color
        self.mss = []

    def add_milestone(self, ms):
        ms.setcolor(self.color)
        self.mss.append(ms)

    def draw(self, dr, x, bottom, top):

        # Print our name at the bottom
        dr.set_color(self.color)
        dr.text(self.name, x - Milestone.named_radius / float(2),
                doc_height - doc_margin, bold=True, pix=Division.pix_per_name)

        # Make the top and bottom fake milstones and insert them in order
        mtop = Milestone()
        mbottom = Milestone()
        mtop.sety(top)
        mbottom.sety(bottom)

        self.mss.sort(key = lambda ms: ms.mno)

        y = doc_height - doc_margin - Division.pix_per_name

        for ms in self.mss:
            ms.sety(y)
            y -= (SVG.pix_per_char + Milestone.named_radius * 2)

        todraw = [mbottom] + self.mss + [mtop]


        last_ms = None
        for ms in todraw:
            print >> sys.stderr, "Doing: %s" % ms.name
            ms.setx(x)
            ms.draw(dr)
            ms.connect(last_ms, dr)
            last_ms = ms

    def width(self, dr):
        w = 0
        for ms in self.mss:
            tmpw = ms.width(dr)
            if tmpw > w:
                w = tmpw    
        tmpw = dr.text_pixlen(self.name, pix=Division.pix_per_name) - \
               Milestone.named_radius / float(2) + Milestone.text_margin
        if tmpw > w:
            w = tmpw
        return w

class Milestone(object):
    named_radius = 9
    named_stroke_width = 3
    line_width = 2
    text_margin = 5
    def __init__(self, month=None, name=None):
        self.name = name
        self.mno = mno_from_mo(month)
        self.yno = yno_from_mo(month)
        self.x = None
        self.y = None
        self.color = None

        if self.mno:
            self.name = '%d: %s' % (self.mno, self.name)

    def setx(self, x):
        self.x = x

    def sety(self, y):
        self.y = y

    def setcolor(self, color):
        self.color = color

    def radius(self):
        if self.name:
            return Milestone.named_radius
        else:
            return 1

    def stroke_width(self):
        if self.name:
            return Milestone.named_stroke_width
        else:
            return 1

    def top(self):
        return self.y - self.radius()

    def bottom(self):
        return self.y + self.radius()

    def textx(self):
        return self.x + self.radius() + Milestone.text_margin

    def width(self, dr):
        # Width is radius of the circle, margin on each side of the text, and the text
        return self.radius() + 2 * Milestone.text_margin + dr.text_pixlen(self.name)

    def draw(self, dr):
        r = self.radius()
        sw = self.stroke_width()
        dr.circle(self.x, self.y, r, sw)
        if self.name:
            dr.text(self.name, self.textx(), self.y + self.radius() / 2)

    def connect(self, other, dr):
        if other:
            x = self.x
            if self.y < other.y:
                y1 = other.top()
                y2 = self.bottom()
            else:
                y1 = other.bottom()
                y2 = self.top()

            dr.line(x, y1, x, y2, Milestone.line_width)

def draw_months(dr, gi):
    dr.line(0, gi.bottom, dr.width, gi.bottom)

def main():
    global doc_margin, doc_height

    #
    # Read from conf file
    #
    roadmap = json.load(open(conf_file))
    roadmap = roadmap["Roadmap"]

    #
    # Make the Drawing
    #
    dr = SVG()

    #
    # Set up the divisions
    #
    divs = []

    for division in roadmap:
        div = Division(division["name"], division["color"])
        divs.append(div)

        for k in division["Milestones"]:
            div.add_milestone(Milestone(k, division["Milestones"][k]))
    #
    # Figure out sizes
    #
    x = doc_margin
    for div in divs:
        x += div.width(dr)
    x += doc_margin

    gi = calc_graph_info(divs)

    dr.create(x, doc_height)

    # Calculate the regions
    x = doc_margin
    gi.bottom = doc_height - Milestone.named_radius - doc_margin
    top = Milestone.named_radius

    # Draw the months
    draw_months(dr, gi)

    # Draw all the divisions
    for div in divs:
        div.draw(dr, x, gi.bottom, top)
        x += div.width(dr)

    dr.close()

if __name__ == '__main__':
    main()
