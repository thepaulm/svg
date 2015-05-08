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

def print_js(idn):
    print '''
<script>
var elemCount = %d;
var hgrowth = 25;
var vgrowth = 6;
var tsize = 12;
var tgrowth = 4;
var font = "font-family:monospace;font-size:";

function fixBoxLength(tElem, rElem, sElem) {
    len = tElem.getComputedTextLength();

    off = Number(tElem.getAttribute("x")) - Number(rElem.getAttribute("x"));
    len += 2 * off;

    rElem.setAttribute("width", len);
    sElem.setAttribute("width", len);
}
function enhanceText(elem) {
    bigtsize = tsize + tgrowth;
    fstring = font + bigtsize + "px;";
    elem.setAttribute("style", fstring);
}
function dehanceText(elem) {
    fstring = font + tsize + "px;";
    elem.setAttribute("style", fstring);
}
function enhanceRect(elem) {
    x = Number(elem.getAttribute("x"));
    y = Number(elem.getAttribute("y"));
    w = Number(elem.getAttribute("width"));
    h = Number(elem.getAttribute("height"));

    elem.setAttribute("origX", x);
    elem.setAttribute("origY", y);
    elem.setAttribute("origW", w);
    elem.setAttribute("origH", h);

    elem.setAttribute("width", w + 2 * hgrowth);
    elem.setAttribute("y", y - vgrowth);
    elem.setAttribute("height", h + 2 * vgrowth);
}
function dehanceRect(elem) {
    elem.setAttribute("y", elem.getAttribute("origY"));
    elem.setAttribute("width", elem.getAttribute("origW"));
    elem.setAttribute("height", elem.getAttribute("origH"));
}
function fireIn(elem) {
    enhanceRect(elem);

    shad = document.getElementById(elem.getAttribute("shadow"));
    enhanceRect(shad);

    text = document.getElementById(elem.getAttribute("text"));
    enhanceText(text);

    tlink = document.getElementById(elem.getAttribute("tlink"));
    if (tlink) {
        enhanceText(tlink);
    }

    fixBoxLength(text, elem, shad);
}
function fireOut(elem) {
    dehanceRect(elem);

    shad = document.getElementById(elem.getAttribute("shadow"));
    dehanceRect(shad);

    text = document.getElementById(elem.getAttribute("text"));
    dehanceText(text);

    tlink = document.getElementById(elem.getAttribute("tlink"));
    if (tlink) {
        dehanceText(tlink);
    }

    fixBoxLength(text, elem, shad);
}
function isElemEnhanced(elem) {
    enhance = elem.getAttribute("enhance");
    if (enhance == "false")
        return false;
    return true;
}
function setElemEnhance(elem, enhance) {
    elem.setAttribute("enhance", enhance);
}
function listenElem(elem, telem, tlelem, evt) {
    enhance = isElemEnhanced(elem);
    if (evt.toElement == elem || evt.toElement == telem ||
       (tlelem != null && evt.toElement == tlelem)) {
        if (!enhance) {
            setElemEnhance(elem, true);
            fireIn(elem);
        }
    } else {
        if (enhance) {
            setElemEnhance(elem, false);
            fireOut(elem);
        }
    }
}
function makeListenElem(elem, telem, tlelem) {
    return function(evt) {
        listenElem(elem, telem, tlelem, evt);
    }
}
function registerElem(elemName) {
    rName = "rect_" + elemName;
    sName = "shad_" + elemName;
    tName = "text_" + elemName;
    tlName = "tlink_" + elemName;
    elem = document.getElementById(rName);
    selem = document.getElementById(sName);
    setElemEnhance(elem, false);
    elem.setAttribute("shadow", sName);
    elem.setAttribute("text", tName);
    elem.setAttribute("tlink", tlName);
    telem = document.getElementById(tName);
    tlelem = document.getElementById(tlName);
    f = makeListenElem(elem, telem, tlelem);
    elem.addEventListener('mouseover', f, false);
    elem.addEventListener('mouseout', f, false);
    telem.addEventListener('mouseover', f, false);
    telem.addEventListener('mouseout', f, false);

    fixBoxLength(telem, elem, selem);
}
(function() {
    var i;
    for (i = 0; i < elemCount; i++) {
        registerElem(i);
    }
})();
</script>
''' % idn

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
        self.months = []
        self.bottom = 0
        self.top = 0
        self.width = 0
        self.height = 0
        self.mo_height = 0
        self.ms_margin = Division.pix_per_name / float(2)
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
    mheight = []
    for d in divs:
        c = {}
        for ms in d.mss:
            if ms.yno == e_year and ms.mno < e_month:
                e_month = ms.mno
            if ms.yno == l_year and ms.mno > l_month:
                l_month = ms.mno
            c[(ms.yno, ms.mno)] = c.get((ms.yno, ms.mno), 0) + ms.height()
        mheight.append(max(c.values()))

    gi.mo_height = max(mheight)

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

    def text(self, s, x, y, bold=False, pix=0, vertical=False, tid=None):
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

    def link(self, x, y, name, url, lid=None):
        pass

class SVG(Drawing):
    pix_per_char = 12
    grid_spaces = 21
    shadow_offset = 4

    def __init__(self):
        super(SVG, self).__init__()
        self.idn = 0

    def get_idn(self):
        idn = self.idn
        self.idn += 1
        return idn

    def text(self, s, x, y, bold=False, pix=pix_per_char, vertical=False, tid=None):
        global text_background
        weight = ""
        writing_mode = ""
        if bold:
            weight = "font-weight: bold;"
        if vertical:
            writing_mode = "writing-mode: tb;"

        style = "font-family:monospace;font-size:%dpx;%s%s" % (pix, weight, writing_mode)
        if pix != SVG.pix_per_char:
            print '<text style="%s" x="%d" y="%d" fill="%s">%s</text>' %\
                (style, x + 1, y + 1, "black", s)
        ids = ""
        if tid:
            ids = 'id = "%s"' % tid
        print '<text %s style="%s" x="%d" y="%d" fill="%s">%s</text>' %\
              (ids, style, x, y, self.color, s)

    def link(self, x, y, name, url, lid=None):
        print '<a xlink:href="%s" target="_blank">' % url
        tid = "t" + lid
        self.text(name, x, y, tid=tid)
        print '</a>'

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

    def rect(self, x, y, width, height, fill, idn=None):
        if not idn:
            idn = ''
        else:
            idn = 'id = "%s"' % idn
        print '<rect %s x="%d" y="%d" width="%d" height="%d" fill="%s" stroke="black" />' %\
              (idn, x, y, width, height, fill)

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
        self.x = 0

    def add_milestone(self, ms):
        ms.setcolor(self.color)
        self.mss.append(ms)

    def draw(self, dr, gi):
        x = self.x

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
            this_vspace = 0
            for ms in self.mss:
                if m.mo == ms.mno and m.yr == ms.yno:
                    thismoms.append(ms)
                    this_vspace += ms.height()

            # y for the milestone is the top milestone in this month
            msy = y - gi.mo_height + this_vspace
            first = True
            for ms in thismoms:
                if not first:
                    msy -= ms.height()
                first = False
                ms.sety(msy)

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
    line_width = 8
    text_margin = 5
    def __init__(self, month=None, name=None, rfc=None):
        self.name = name
        self.mno = mno_from_mo(month)
        self.yno = yno_from_mo(month)
        self.x = None
        self.y = None
        self.color = None
        print >> sys.stderr, "GOT MY RFC"
        self.RFCUrl = rfc
        self.PhabTicket = None

    # For sorting: Make a number that includes year and then month
    def key(self):
        return self.yno * 100 + self.mno

    def height(self):
        linecount = 1
        if self.RFCUrl:
            linecount += 1
        pix = SVG.pix_per_char
        ms_margin = Division.pix_per_name / float(2)
        return (ms_margin * 2 + linecount * pix * 1.5)

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
            pix = SVG.pix_per_char
            x = self.textx()
            y = self.y + self.radius() / 2
            rx = x - pix / float(2)
            ry = y - pix
            idn = dr.get_idn()
            linecount = 1
            if self.RFCUrl:
                linecount += 1

            dr.rect(rx + SVG.shadow_offset, ry + SVG.shadow_offset,
                    dr.text_pixlen(self.name + 'a'), linecount * pix * 1.5, "black",
                    idn="shad_" + str(idn))
            dr.rect(rx, ry, dr.text_pixlen(self.name + 'a'), linecount * pix * 1.5,
                    text_background, idn="rect_" + str(idn))

            dr.text(self.name, x, y, tid="text_%d" % idn)
            if self.RFCUrl:
                dr.link(x, y + 1.5 * pix, "(RFC)", self.RFCUrl, lid="link_%d" % idn)

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
                    name = k
                    body = division["Milestones"][name]
                    date = None
                    rfc = None
                    try:
                        date = body["Date"]
                    except:
                        date = body
                    try:
                        rfc = body["RFC"]
                    except:pass
                    div.add_milestone(Milestone(date, name, rfc=rfc))
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
        div.x = x
        x += div.width(dr)

    while len(divs):
        div = divs.pop()
        div.draw(dr, gi)

    print_js(dr.idn);

    dr.close()

if __name__ == '__main__':
    main()
