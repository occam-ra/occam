from enum import Enum
from typing import Union


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
        self._ref = ref
        self._id = 0

    def __lt__(self, other: 'Model') -> bool:
        return self.name < other.name

    @property
    def ref(self):
        return self._ref

    @property
    def name(self) -> str:
        return self.get_attribute_value("name")

    @property
    def print_name(self) -> str:
        return self._ref.getPrintName()

    @property
    def id_(self) -> int:
        return self._id

    @id_.setter
    def id_(self, id_):
        self._id = id_

    @property
    def fit_table(self):
        pass

    @fit_table.setter
    def fit_table(self, model):
        self._ref.makeFitTable(model)

    @fit_table.deleter
    def fit_table(self):
        self._ref.deleteFitTable()

    def set(self, **kwargs):
        pass

    def set_id(self, id_: int) -> None:
        self._ref.setID(id_)

    def set_progenitor(self, progenitor: 'Model') -> None:
        self._ref.setProgenitor(progenitor.ref)

    def get_attribute_value(self, attribute: str) -> Union[str, float]:
        return self._ref.get(attribute)

    def is_is_equivalent_to(self, model: 'Model') -> bool:
        return self._ref.isEquivalentTo(model.ref)

    def delete_fit_table(self) -> None:
        self._ref.deleteFitTable()
