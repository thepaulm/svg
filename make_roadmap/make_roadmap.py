#!/usr/bin/env python

import sys
import json

doc_width = 800
doc_height = 400
start_x = 50
conf_file = 'roadmap.json'

class Drawing(object):
    def __init__(self):
        pass

    def set_color(self, c):
        self.color = c

    def line(self, x1, y1, x2, y2, lw):
        pass

    def text(self, s, x, y):
        pass

    def circle(self, x, y, r, sw):
        pass

    def create(self):
        pass

    def close(self):
        pass

class SVG(Drawing):
    def __init__(self):
        super(SVG, self).__init__()

    def text(self, s, x, y):
        print '<text x="%d" y="%d" fill="%s">%s</text>' %\
            (x, y, self.color, s)

    def create(self, x, y):
        print '<?xml version="1.0" encoding="UTF-8" standalone="no"?>'
        print '<svg width="%d" height="%d" xmlns="http://www.w3.org/2000/svg">' % (x, y)

    def circle(self, x, y, r, sw):
        print '<circle cx="%d" cy="%d" r="%d" stroke="%s" stroke-width="%d" fill="white" />' %\
            (x, y, r, self.color, sw)

    def line(self, x1, y1, x2, y2, lw):
        print '<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="%d" />' %\
            (x1, y1, x2, y2, self.color, lw)

    def close(self):
        print '</svg>'

class Division(object):
    def __init__(self, name, color, startx):
        self.name = name
        self.color = color
        self.startx = startx
        self.mss = []

    def add_milestone(self, ms):
        ms.setx(self.startx)
        ms.setcolor(self.color)
        self.mss.append(ms)

    def draw(self, dr):

        dr.set_color(self.color)
        dr.text(self.name, self.startx, doc_height)

        last_ms = None
        for ms in self.mss:
            ms.draw(dr)
            ms.connect(last_ms, dr)
            last_ms = ms

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
    global doc_width, doc_height

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
    division_x = start_x

    for division in roadmap:
        div = Division(division["name"], division["color"], division_x)
        divs.append(div)
        division_x += 200

        div.add_milestone(Milestone(doc_height - Milestone.named_radius))
        div.add_milestone(Milestone(100, "Bar thing"))
        div.add_milestone(Milestone(50, "Foo thing"))
        div.add_milestone(Milestone(Milestone.named_radius))

    dr.create(doc_width, doc_height)

    for div in divs:
        div.draw(dr)

    dr.close()

if __name__ == '__main__':
    main()
