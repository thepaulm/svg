#!/usr/bin/env python

import sys
import json

doc_height = 400
doc_margin = 20
start_x = 50
conf_file = 'roadmap.json'

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

    def text_pixlen(self, s):
        if not s:
            return 0
        return len(s) * SVG.pix_per_char

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

    def circle(self, x, y, r, sw):
        print '<circle cx="%d" cy="%d" r="%d" stroke="%s" stroke-width="%d" fill="white" />' %\
            (x, y, r, self.color, sw)

    def line(self, x1, y1, x2, y2, lw=1):
        print '<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="%d" />' %\
            (x1, y1, x2, y2, self.color, lw)

    def close(self):
        print '</svg>'

class Division(object):
    def __init__(self, name, color):
        self.name = name
        self.color = color
        self.mss = []

    def add_milestone(self, ms):
        ms.setcolor(self.color)
        self.mss.append(ms)

    def draw(self, dr, x):

        dr.set_color(self.color)
        dr.text(self.name, x, doc_height, bold=True, pix=18)

        last_ms = None
        for ms in self.mss:
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

        return w

class Milestone(object):
    named_radius = 9
    named_stroke_width = 3
    line_width = 2
    text_margin = 5
    def __init__(self, y, name=None):
        self.y = y
        self.name = name
        self.x = None
        self.color = None

    def setx(self, x):
        self.x = x

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
            dr.text(self.name, self.textx(), self.bottom())

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

        y = 50
        div.add_milestone(Milestone(doc_height - Milestone.named_radius))
        for k in division["Milestones"]:
            div.add_milestone(Milestone(doc_height - y, division["Milestones"][k]))
            y += 50
        div.add_milestone(Milestone(Milestone.named_radius))

    #
    # Figure out sizes
    #
    x = doc_margin
    for div in divs:
        x += div.width(dr)
    x += doc_margin

    dr.create(x, doc_height)

    x = doc_margin
    for div in divs:
        div.draw(dr, x)
        x += div.width(dr)

    dr.close()

if __name__ == '__main__':
    main()
