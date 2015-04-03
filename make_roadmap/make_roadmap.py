#!/usr/bin/env python

import sys
import json
import re
import string
import glob
import codecs

doc_margin = 20
start_x = 50
doc_background = "#eeeeee"
text_background = "#fefefe"
grid_color = "#cfcfcf"

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

    def qstr(self):
        return "Q%d %d" % (mo_to_quarter(self.mo), self.yr)

class GraphInfo(object):
    def __init__(self):
        self.ms_per_mo = None
        self.months = []
        self.bottom = 0
        self.top = 0
        self.width = 0
        self.height = 0
        self.mo_height = 0
        self.ms_margin = Division.pix_per_name / float(2)
        self.ms_vspace = 0
        self.left = 0

def mo_to_quarter(mo):
    return (mo + 2) / 3

def first_mo_of_quarter(q):
    return (q - 1) * 3 + 1

def calc_graph_info(divs, dr):
    global doc_margin

    gi = GraphInfo()

    e_year = 9999
    l_year = 0
    gi.left = 2 * dr.pix_per_char
    width = gi.left

    # Find first and last year
    for d in divs:
        width += d.width(dr)
        for ms in d.mss:
            if ms.yno < e_year:
                e_year = ms.yno
            if ms.yno > l_year:
                l_year = ms.yno
    width += doc_margin
    gi.width = width

    # Find first and last months and the counts per month
    e_month = 13
    l_month = 0
    m = []
    for d in divs:
        c = {}
        for ms in d.mss:
            if ms.yno == e_year and ms.mno < e_month:
                e_month = ms.mno
            if ms.yno == l_year and ms.mno > l_month:
                l_month = ms.mno
            c[(ms.yno, ms.mno)] = c.get((ms.yno, ms.mno), 0) + 1
        m.append(max(c.values()))

    gi.ms_per_mo = max(m)

    # Convert to first month of the quarter
    quarter = mo_to_quarter(e_month)
    e_month = first_mo_of_quarter(quarter)
    # Convert to the last month of the quarter
    quarter = mo_to_quarter(l_month)
    l_month = first_mo_of_quarter(quarter) + 2

    # Build months list
    z = Month(e_year, e_month)
    while z != (l_year, l_month):
        gi.months.append(z)
        z = z + 1
    gi.months.append(z)

    for m in gi.months:
        print >> sys.stderr, m

    # Figure the y space for the drawing part
    bottom_offset = 2 * Milestone.named_radius + doc_margin
    top_offset = Milestone.named_radius

    gi.ms_vspace = (gi.ms_margin * 2 + Milestone.named_radius * 2)
    gi.mo_height = gi.ms_per_mo * gi.ms_vspace
    gi.height = len(gi.months) * gi.mo_height + bottom_offset + top_offset
    gi.bottom = gi.height - bottom_offset
    gi.top = Milestone.named_radius

    return gi

class Drawing(object):
    pix_per_char = 0

    def __init__(self):
        self.colorstack = []
        self.color = None

    def set_color(self, c):
        self.color = c

    def push_color(self, c):
        self.colorstack.append(self.color)
        self.color = c

    def pop_color(self):
        self.color = self.colorstack.pop()

    def line(self, x1, y1, x2, y2, lw):
        pass

    def text(self, s, x, y, bold=False, pix=0):
        pass

    def text_pixlen(self, s):
        return 0

    def circle(self, x, y, r, sw):
        pass

    def rect(self, x, y, width, height, fill):
        pass

    def create(self):
        pass

    def close(self):
        pass

class SVG(Drawing):
    pix_per_char = 12
    grid_spaces = 21
    shadow_offset = 4

    def __init__(self):
        super(SVG, self).__init__()

    def text(self, s, x, y, bold=False, pix=pix_per_char, vertical=False):
        global text_background
        weight = ""
        writing_mode = ""
        if bold:
            weight = "font-weight: bold;"
        if vertical:
            writing_mode = "writing-mode: tb;"
        if not vertical and pix == SVG.pix_per_char:
            rx = x - pix / float(2)
            ry = y - pix
            self.rect(rx + SVG.shadow_offset, ry + SVG.shadow_offset,
                      self.text_pixlen(s + 'a'), pix * 1.5, "black")
            self.rect(rx, ry, self.text_pixlen(s + 'a'), pix * 1.5, text_background)

        style = "font-family:monospace;font-size:%dpx;%s%s" % (pix, weight, writing_mode)
        if pix != SVG.pix_per_char:
            print '<text style="%s" x="%d" y="%d" fill="%s">%s</text>' %\
                (style, x + 1, y + 1, "black", s)
        print '<text style="%s" x="%d" y="%d" fill="%s">%s</text>' %\
            (style, x, y, self.color, s)

    def text_pixlen(self, s, pix=pix_per_char):
        if not s:
            return 0
        return len(s) * (pix * (float(2)/float(3)))

    def grid(self, gi):
        global grid_color
        self.push_color(grid_color)
        at = gi.left
        while at < gi.width:
            self.line(at, 0, at, gi.bottom)
            at += SVG.grid_spaces
        at = 0
        while at < gi.bottom:
            self.line(gi.left, at, gi.width, at)
            at += SVG.grid_spaces
        self.pop_color()

    def create(self, x, y):
        global doc_background
        print '<!DOCTYPE html>'
        print '<head>'
        print '<meta charset="UTF-8">'
        print '</head>'
        print '<html>'
        print '<body>'
        print '<svg width="%d" height="%d" style="background: %s">' % (x, y, doc_background)

        self.width = x
        self.height = y

    def rect(self, x, y, width, height, fill):
        print '<rect x="%d" y="%d" width="%d" height="%d" fill="%s" stroke="black" />' %\
              (x, y, width, height, fill)

    def circle(self, x, y, r, sw):
        print '<circle cx="%d" cy="%d" r="%d" stroke="%s" stroke-width="%d" fill="white" />' %\
            (x, y, r, self.color, sw)

    def line(self, x1, y1, x2, y2, lw=1, dash=False):
        strokebits = 'stroke="%s" stroke-width="%d"' % (self.color, lw)
        if dash:
            print '<path stroke-dasharray="10,10" d="M%d %d L%d %d" %s />' %\
                (x1, y1, x2, y2, strokebits)
        else:
            print '<line x1="%d" y1="%d" x2="%d" y2="%d" %s />' %\
                (x1, y1, x2, y2, strokebits)

    def close(self):
        print '</svg>'
        print '</body>'
        print '</html>'


class Division(object):
    pix_per_name = 18

    def __init__(self, name, color):
        self.name = name
        self.color = color
        self.mss = []

    def add_milestone(self, ms):
        ms.setcolor(self.color)
        self.mss.append(ms)

    def draw(self, dr, x, gi):

        # Print our name at the bottom
        dr.set_color(self.color)
        dr.text(self.name, x - Milestone.named_radius / float(2),
                gi.height - doc_margin, bold=False, pix=Division.pix_per_name)

        # Make the top and bottom fake milstones and insert them in order
        mtop = Milestone()
        mbottom = Milestone()
        mtop.sety(gi.top)
        mbottom.sety(gi.bottom)

        self.mss.sort(key = lambda ms: ms.key())

        y = gi.bottom - gi.ms_margin - Milestone.named_radius

        # Draw the milestones in their month locations
        for m in gi.months:
            thismoms = []
            for ms in self.mss:
                if m.mo == ms.mno and m.yr == ms.yno:
                    thismoms.append(ms)

            # y for the milestone is the top milestone in this month
            msy = y - (gi.ms_per_mo - 1) * gi.ms_vspace + (len(thismoms) - 1) * gi.ms_vspace
            for ms in thismoms:
                    ms.sety(msy)
                    # Next milestone in this month will be one slot down
                    msy -= gi.ms_vspace

            y -= gi.mo_height

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

        #if self.mno:
            #self.name = '%d: %s' % (self.mno, self.name)

    # For sorting: Make a number that includes year and then month
    def key(self):
        return self.yno * 100 + self.mno

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
        if self.name:
            dr.text(self.name, self.textx(), self.y + self.radius() / 2)
        r = self.radius()
        sw = self.stroke_width()
        dr.circle(self.x, self.y, r, sw)

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
    dr.push_color("black")
    y = gi.bottom
    dr.line(0, y, dr.width, y)
    for m in gi.months:
        y -= gi.mo_height
        # Only draw the quarter marks
        if m.mo % 3 == 0:
            dr.line(0, y, dr.width, y, dash=True)
            dr.text(m.qstr(), dr.pix_per_char, y + doc_margin, vertical=True)
    dr.pop_color()

def main():
    #
    # Set up the divisions
    #
    divs = []

    # Read each of the json files
    for rmf in glob.glob('./*.json'):
        try:
            roadmap = json.load(open(rmf))
            roadmap = roadmap["Roadmap"]

            for division in roadmap:
                div = Division(division["name"], division["color"])
                divs.append(div)

                for k in division["Milestones"]:
                    div.add_milestone(Milestone(division["Milestones"][k], k))
        except Exception, e:
            print >> sys.stderr, "%s: " % rmf, e

    #
    # Make the Drawing
    #
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout)
    dr = SVG()

    #
    # Figure out sizes
    #
    gi = calc_graph_info(divs, dr)
    dr.create(gi.width, gi.height)

    # Calculate the regions
    dr.grid(gi)

    # Draw the months
    draw_months(dr, gi)

    # Draw all the divisions
    x = gi.left + Milestone.named_radius
    for div in divs:
        div.draw(dr, x, gi)
        x += div.width(dr)

    dr.close()

if __name__ == '__main__':
    main()
