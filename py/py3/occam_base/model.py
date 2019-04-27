from enum import Enum


class ModelType(Enum):
    TOP = 'top'
    BOTTOM = 'bottom'
    DEFAULT = 'default'


class Model:
    """
    Wrapper class for Model
    """

    def __init__(self, ref=None) -> None:
        """
        :param: ref: the reference to the Model object returned from the CPP engine
        """
        # Create new reference if one not given
        self._ref = ref
        self._id = 0

    @property
    def id_(self) -> int:
        return self._id

    @id_.setter
    def id_(self, id_: int) -> None:
        self._id = id_

    @property
    def fit_table(self) -> None:
        pass

    @fit_table.setter
    def fit_table(self, model) -> None:
        self._ref.makeFitTable(model)

    @fit_table.deleter
    def fit_table(self):
        self._ref.deleteFitTable()

    def set(self, **kwargs):
        pass

    @property
    def print_name(self) -> str:
        return self._ref.getPrintName()

    def get_ref(self):
        return self._ref
