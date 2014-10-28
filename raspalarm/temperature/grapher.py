#!/usr/bin/env python
import datetime
import os

from raspalarm.conf import settings

def create(x, y, out='graph.png'):
    # We want to avoid importing matplotlib unless we are going to use it
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.figure()
    plt.locator_params(nbins=4, axis='x')
    plt.plot(x, y)
    plt.savefig(out)
    return out

def get_filename(dt=datetime.datetime.now):
    if callable(dt):
        dt = dt()
    d = os.path.join(
        settings.BASE_DIR,
        settings.TEMPERATURE_GRAPH_DIR
    )
    if not os.path.exists(d):
        os.makedirs(d)
    return os.path.join(
        d,
        '%s.png' % dt.strftime('%y%m%d')
    )

if __name__ == '__main__':
    x = [0, 1, 2, 3, 4, 5]
    y = [xi**2 for xi in x]
    create(x, y)
