from decimal import Decimal

from agate.aggregations.base import Aggregation
from agate.aggregations.has_nulls import HasNulls
from agate.aggregations.mean import Mean
from agate.data_types import Number, TimeDelta
from agate.exceptions import DataTypeError
from agate.warns import warn_null_calculation


class _DeviationAggregation(Aggregation):
    """
    Shared implementation for the variance and standard deviation families.

    Subclasses only describe how they differ: whether the sample (``n - 1``)
    or population (``n``) denominator is used, and which inner aggregation
    they wrap. The column type check, null handling and empty-column
    semantics live here so the four public aggregations can not drift apart.
    """
    #: When ``True`` the sample denominator (``n - 1``) is used, otherwise
    #: the population denominator (``n``) is used.
    _sample = True

    def __init__(self, column_name):
        self._column_name = column_name
        self._mean = Mean(column_name)

    def get_aggregate_data_type(self, table):
        column = table.columns[self._column_name]

        if isinstance(column.data_type, Number):
            return Number()

        if isinstance(column.data_type, TimeDelta):
            return self._get_timedelta_data_type()

    def _get_timedelta_data_type(self):
        return Number()

    def validate(self, table):
        column = table.columns[self._column_name]

        if not isinstance(column.data_type, (Number, TimeDelta)):
            raise DataTypeError(
                '{} can only be applied to columns containing Number or TimeDelta data.'.format(
                    self.__class__.__name__
                )
            )

        has_nulls = HasNulls(self._column_name).run(table)

        if has_nulls:
            warn_null_calculation(self, column)

    def run(self, table):
        column = table.columns[self._column_name]

        data = column.values_without_nulls()
        if not data:
            return None

        mean = self._mean.run(table)
        denominator = len(data) - 1 if self._sample else len(data)

        if isinstance(column.data_type, TimeDelta):
            return self._run_timedelta(data, mean, denominator)

        return sum((n - mean) ** 2 for n in data) / Decimal(denominator)

    def _run_timedelta(self, data, mean, denominator):
        # A timedelta can not be squared, so the deviations are measured in
        # seconds and converted to Decimals before the same sum / denominator
        # calculation used for Number columns.
        squared_deviations = sum(
            (Decimal(str((n - mean).total_seconds())) ** 2) for n in data
        )

        return squared_deviations / Decimal(denominator)


class Variance(_DeviationAggregation):
    """
    Calculate the sample variance of a column.

    For the population variance see :class:`.PopulationVariance`.

    When applied to a :class:`.TimeDelta` column, the variance is calculated on
    the values expressed in seconds and a :class:`.Number` of seconds squared
    is returned, since a squared :class:`datetime.timedelta` is not defined.

    :param column_name:
        The name of a column containing :class:`.Number` or :class:`.TimeDelta` data.
    """
    _sample = True


class PopulationVariance(Variance):
    """
    Calculate the population variance of a column.

    For the sample variance see :class:`.Variance`.

    When applied to a :class:`.TimeDelta` column, the variance is calculated on
    the values expressed in seconds and a :class:`.Number` of seconds squared
    is returned, since a squared :class:`datetime.timedelta` is not defined.

    :param column_name:
        The name of a column containing :class:`.Number` or :class:`.TimeDelta` data.
    """
    _sample = False
