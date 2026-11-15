import datetime

from agate.aggregations.variance import PopulationVariance, Variance, _DeviationAggregation
from agate.data_types import TimeDelta


class _StDevAggregation(_DeviationAggregation):
    """
    Shared implementation for the standard deviation family.

    The variance calculation (column type check, null handling, sample and
    population denominators) is inherited from :class:`._DeviationAggregation`;
    only the square-root step is added here. Subclasses select the sample or
    population result through :attr:`_variance_class`.
    """
    #: The variance aggregation wrapped by this standard deviation.
    _variance_class = Variance

    def _get_timedelta_data_type(self):
        return TimeDelta()

    def run(self, table):
        variance = self._variance_class(self._column_name).run(table)
        if variance is None:
            return None

        if isinstance(table.columns[self._column_name].data_type, TimeDelta):
            return datetime.timedelta(seconds=float(variance.sqrt()))

        return variance.sqrt()


class StDev(_StDevAggregation):
    """
    Calculate the sample standard of deviation of a column.

    For the population standard of deviation see :class:`.PopulationStDev`.

    When applied to a :class:`.TimeDelta` column, the underlying
    :class:`.Variance` is calculated on the values expressed in seconds and a
    :class:`datetime.timedelta` is returned.

    :param column_name:
        The name of a column containing :class:`.Number` or :class:`.TimeDelta` data.
    """
    _variance_class = Variance


class PopulationStDev(StDev):
    """
    Calculate the population standard of deviation of a column.

    For the sample standard of deviation see :class:`.StDev`.

    When applied to a :class:`.TimeDelta` column, the underlying
    :class:`.PopulationVariance` is calculated on the values expressed in
    seconds and a :class:`datetime.timedelta` is returned.

    :param column_name:
        The name of a column containing :class:`.Number` or :class:`.TimeDelta` data.
    """
    _variance_class = PopulationVariance
