#!/usr/bin/env python

doc_width = 200
doc_height = 400

class Milestone(object):
    named_radius = 9
    named_stroke_width = 3
    line_width = 2
    text_margin = 5
    def __init__(self, x, y, color, name=None):
        self.x = x
        self.y = y
        self.color = color
        self.name = name

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
    make_header(doc_width, doc_height)

    mss = []
    mss.append(Milestone(50, doc_height - Milestone.named_radius, "red"))
    mss.append(Milestone(50, 100, "red", "Bar thing"))
    mss.append(Milestone(50, 50, "red", "Foo thing"))
    mss.append(Milestone(50, Milestone.named_radius, "red"))
    last_ms = None
    for ms in mss:
        ms.draw()
        ms.connect(last_ms)
        last_ms = ms
    make_close()

if __name__ == '__main__':
    main()
