
import schemdraw
from schemdraw import flow

# Set default flowchart box fill colors
flow.Box.defaults['fill'] = '#eeffff'
flow.Start.defaults['fill'] = '#ffeeee'
flow.Decision.defaults['fill'] = '#ffffee'

with schemdraw.Drawing() as d:
    d.config(unit=.75)
    flow.Start(h=1.5).label('Select\n$N>1$').drop('S')
    flow.Arrow().down()
    flow.Box().label('Let k=2\nLet $n=N$')
    flow.Arrow()
    k2 = flow.Decision(E='Yes', S='No').label('Is $k^2 < n$?').drop('E')
    flow.Arrow().length(1)
    flow.Box().label('Add final\nelement\nto dictionary').drop('S')
    flow.Arrow().down()
    flow.Start().label('Stop')
    flow.Arrow().at(k2.S)
    kn = flow.Decision(W='No', S='Yes').label('Is $k$ a\nfactor of $n$?').drop('W')
    flow.Arrow().left().length(1)
    flow.Box().label('Replace $k$\nby $k+1$').drop('N')
    flow.Arrow().toy(k2.W).dot(open=True)
    flow.Arrow().tox(k2.W)

    flow.Arrow().down().at(kn.S)
    flow.Box().label('Replace $n$\nby $n/k$')
    flow.Arrow()
    k3 = flow.Decision(E='No', W='Yes').label('Is $k$ in\ndictionary?').drop('E')

    flow.Arrow().left().at(k3.W).length(1)
    rep = flow.Box().label('Replace $v$\nby $v+1$')
    flow.Arrow()
    dot = flow.Arrow().up().toy(k2.W).dot(open=True)
    flow.Arrow().right().tox(rep.N)

    flow.Arrow().at(k3.E).right().length(1)
    flow.Box().label('Add $k$ to\ndictionary\nwith $v=1$').drop('S')
    flow.Arrow().down()
    flow.Arrow().left().to(rep.W, dx=-1.5)
    flow.Arrow().up().toy(k2.W)
    flow.Arrow().right().tox(dot.center)


