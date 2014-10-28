#!/usr/bin/env python
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def create(x, y, out='graph.png'):
    plt.figure()
    plt.locator_params(nbins=4, axis='x')
    plt.plot(x, y)
    plt.savefig(out)
    return out


if __name__ == '__main__':
    x = [0, 1, 2, 3, 4, 5]
    y = [xi**2 for xi in x]
    create(x, y)
