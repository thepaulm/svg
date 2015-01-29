#!/usr/bin/env python

import sys
import json

doc_width = 800
doc_height = 400
start_x = 50
conf_file = 'roadmap.json'

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

    def draw(self):

        print '<text x="%d" y="%d" fill="%s">%s</text>' %\
            (self.startx, doc_height, self.color, self.name)

        last_ms = None
        for ms in self.mss:
            ms.draw()
            ms.connect(last_ms)
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

    def draw(self):
        r = self.radius()
        sw = self.stroke_width()
        print '<circle cx="%d" cy="%d" r="%d" stroke="%s" stroke-width="%d" fill="white" />' %\
            (self.x, self.y, r, self.color, sw)
        if self.name:
            print '<text x="%d" y="%d" fill="%s">%s</text>' %\
                (self.textx(), self.bottom(), self.color, self.name)

    def connect(self, other):
        if other:
            x = self.x
            if self.y < other.y:
                y1 = other.top()
                y2 = self.bottom()
            else:
                y1 = other.bottom()
                y2 = self.top()

            print '<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="%d" />' %\
                (x, y1, x, y2, self.color, Milestone.line_width)


def make_header(x, y):
    print '<?xml version="1.0" encoding="UTF-8" standalone="no"?>'
    print '<svg width="%d" height="%d" xmlns="http://www.w3.org/2000/svg">' % (x, y)

def make_close():
    print '</svg>'

def main():
    global doc_width, doc_height

    division_x = start_x

    roadmap = json.load(open(conf_file))

    roadmap = roadmap["Roadmap"]

    divs = []

    for division in roadmap:
        div = Division(division["name"], division["color"], division_x)
        divs.append(div)
        division_x += 200

        div.add_milestone(Milestone(doc_height - Milestone.named_radius))
        div.add_milestone(Milestone(100, "Bar thing"))
        div.add_milestone(Milestone(50, "Foo thing"))
        div.add_milestone(Milestone(Milestone.named_radius))

    make_header(doc_width, doc_height)

    for div in divs:
        div.draw()
    make_close()

if __name__ == '__main__':
    main()
