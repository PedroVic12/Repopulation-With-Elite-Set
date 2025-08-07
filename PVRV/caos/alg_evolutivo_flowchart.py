import schemdraw
from schemdraw import flow

with schemdraw.Drawing() as d:
    d.config(fontsize=11)
    b = flow.Start().label('START')
    flow.Arrow().down(d.unit/2)
    d1 = flow.Decision(w=5, h=3.9, E='YES', S='NO').label('DO YOU\nUNDERSTAND\nFLOW CHARTS?')
    flow.Arrow().length(d.unit/2)
    d2 = flow.Decision(w=5, h=3.9, E='YES', S='NO').label('OKAY,\nYOU SEE THE\nLINE LABELED\n"YES"?')
    flow.Arrow().length(d.unit/2)
    d3 = flow.Decision(w=5.2, h=3.9, E='YES', S='NO').label('BUT YOU\nSEE THE ONES\nLABELED "NO".')

    flow.Arrow().right(d.unit/2).at(d3.E)
    flow.Box(w=2, h=1.25).anchor('W').label('WAIT,\nWHAT?')
    flow.Arrow().down(d.unit/2).at(d3.S)
    listen = flow.Box(w=2, h=1).label('LISTEN.')
    flow.Arrow().right(d.unit/2).at(listen.E)
    hate = flow.Box(w=2, h=1.25).anchor('W').label('I HATE\nYOU.')

    flow.Arrow().right(d.unit*3.5).at(d1.E)
    good = flow.Box(w=2, h=1).anchor('W').label('GOOD')
    flow.Arrow().right(d.unit*1.5).at(d2.E)
    d4 = flow.Decision(w=5.3, h=4.0, E='YES', S='NO').anchor('W').label('...AND YOU CAN\nSEE THE ONES\nLABELED "NO"?')

    flow.Wire('-|', arrow='->').at(d4.E).to(good.S)
    flow.Arrow().down(d.unit/2).at(d4.S)
    d5 = flow.Decision(w=5, h=3.6, E='YES', S='NO').label('BUT YOU\nJUST FOLLOWED\nTHEM TWICE!')
    flow.Arrow().right().at(d5.E)
    question = flow.Box(w=3.5, h=1.75).anchor('W').label("(THAT WASN'T\nA QUESTION.)")
    flow.Wire('n', k=-1, arrow='->').at(d5.S).to(question.S)

    flow.Line().at(good.E).tox(question.S)
    flow.Arrow().down()
    drink = flow.Box(w=2.5, h=1.5).label("LET'S GO\nDRINK.")
    flow.Arrow().right().at(drink.E).label('6 DRINKS')
    flow.Box(w=3.7, h=2).anchor('W').label('HEY, I SHOULD\nTRY INSTALLING\nFREEBSD!')
    flow.Arrow().up(d.unit*.75).at(question.N)
    screw = flow.Box(w=2.5, h=1).anchor('S').label('SCREW IT.')
    flow.Arrow().at(screw.N).toy(drink.S)

    
