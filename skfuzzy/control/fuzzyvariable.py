"""
fuzzyvariable.py : Contains base fuzzy variable class.
"""
import numpy as np
import matplotlib.pyplot as plt
from ..membership import trimf

try:
    from collections import OrderedDict
except ImportError:
    from .ordereddict import OrderedDict


class FuzzyVariable(object):
    """
    Base class containing universe variable & associated membership functions.

    Parameters
    ----------
    universe : array-like
        Universe variable. Must be 1-dimensional and convertible to a NumPy
        array. Required.
    label : string
        Name of the universe variable. Optional.

    Methods
    -------

    Notes
    -----
    This class is designed as the base class underlying the Antecedent and
    Consequent classes, not for individual use.
    """
    def __init__(self, universe, label):
        """
        Initialization of fuzzy variable

        Parameters
        ----------
        universe : array-like
            Universe variable. Must be 1-dimensional and convertible to a NumPy
            array.
        label : string
            Unique name of the universe variable, e.g., 'food' or 'velocity'.
        """
        self.universe = np.asarray(universe)
        self.active = None
        self.mf = OrderedDict()
        self.label = label
        self.connections = OrderedDict()
        self._id = id(self)
        self.output = None

    def __getitem__(self, key):
        """
        Calling variable['label'] will activate 'label' membership function.
        """
        if key in self.mf:
            self.active = key
            return self
        else:
            # Build a pretty list of available mf labels and raise an
            # informative error message
            options = ''
            i0 = len(self.mf) - 1
            i1 = len(self.mf) - 2
            for i, available_key in enumerate(self.mf.iterkeys()):
                if i == i1:
                    options += "'" + str(available_key) + "', or "
                elif i == i0:
                    options += "'" + str(available_key) + "'."
                else:
                    options += "'" + str(available_key) + "'; "
            raise ValueError("Membership function '{0}' does not exist for "
                             "{1} {2}.\n"
                             "Available options: {3}".format(
                                 key, self.__name__, self.label, options))

    def __setitem__(self, key, item):
        """
        Enables new membership functions to be added with the syntax::

          variable['new_label'] = new_mf
        """
        mf = np.asarray(item)
        if mf.size != self.universe.size:
            raise ValueError("New membership function {0} must be equivalent "
                             "in length to the universe variable.\n"
                             "Expected {1}, got {2}.".format(
                                 key, self.universe.size, item.size))
        self.mf[key] = item

    def _variable_figure_generator(self, *args, **kwargs):
        self._fig, self._ax = plt.subplots()
        self._plots = {}

        self._ax.set_ylim([0, 1])
        self._ax.set_xlim([self.universe.min(), self.universe.max()])

        for key, value in self.mf.iteritems():
            if key == self.active:
                lw = 2
            else:
                lw = 1

            self._plots[key] = self._ax.plot(self.universe,
                                             value,
                                             label=key,
                                             lw=lw)

        self._ax.legend(framealpha=0.5)
        self._ax.tick_params(direction='out')

        if self.label is None:
            label = ''
        else:
            label = self.label

        self._ax.set_ylabel('Membership')
        self._ax.set_xlabel(label)

    def automf(self, number=5, variable_type='quality', invert=False):
        """
        Automatically populates the universe with membership functions.

        Parameters
        ----------
        number : [3, 5, 7]
            Number of membership functions to create. Must be an odd integer.
            At present, only 3, 5, or 7 are supported.
        type : string
            Type of variable this is. Accepted arguments are
            * 'quality' : Continuous variable, higher values are better.
            * 'quant' : Quantitative variable, no value judgements.
        invert : bool
            Reverses the naming order if True.

        Notes
        -----
        This convenience function allows quick construction of fuzzy variables
        with overlapping, triangular membership functions.

        It uses a standard naming convention defined for ``'quality'`` as::

        * dismal
        * poor
        * mediocre
        * average (always middle)
        * decent
        * good
        * excellent

        and for ``'quant'`` as::

        * lowest
        * lower
        * low
        * average (always middle)
        * high
        * higher
        * highest

        where the names on either side of ``'average'`` are used as needed to
        create 3, 5, or 7 membership functions.
        """
        if variable_type.lower() == 'quality':
            names = ['dismal',
                     'poor',
                     'mediocre',
                     'average',
                     'decent',
                     'good',
                     'excellent']
        else:
            names = ['lowest',
                     'lower',
                     'low',
                     'average',
                     'high',
                     'higher',
                     'highest']

        if number == 3:
            names = names[1:6:2]
        if number == 5:
            names = names[1:6]

        if invert is True:
            names = names[::-1]

        if number != 3:
            if number != 5:
                if number != 7:
                    return ValueError("Only number = 3, 5, or 7 supported.")

        limits = [self.universe.min(), self.universe.max()]
        universe_range = limits[1] - limits[0]
        widths = [universe_range / ((number - 1) / 2.)] * int(number)
        centers = np.linspace(limits[0], limits[1], number)

        abcs = [[c - w / 2, c, c + w / 2] for c, w in zip(centers, widths)]

        # Clear existing membership functions, if any
        self.mf = OrderedDict()
        if self.__name__ == 'Antecedent':
            self.output = OrderedDict()
        else:
            self.output = None

        # Repopulate
        for name, abc in zip(names, abcs):
            self[name] = trimf(self.universe, abc)
