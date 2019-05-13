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
        # Create new reference if one not given
        self._ref = ref
        self._id = 0

    def __lt__(self, other: 'Model') -> bool:
        return self.name < other.name

    def __eq__(self, other: 'Model') -> bool:
        return self._ref.isEquivalentTo(other.ref)

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

    def get_struct_matrix(self) -> list:
        return self._ref.getStructMatrix()

    @property
    def ref(self):
        return self._ref

    def is_equivalent_to(self) -> bool:
        return self._ref.isEquivalentTo()

    def set_progenitor(self, progenitor: 'Model') -> None:
        self._ref.setProgenitor(progenitor.ref)

    def get_attribute_value(self, attribute: str) -> Union[str, float]:
        return self._ref.get(attribute)

    def delete_fit_table(self) -> None:
        self._ref.deleteFitTable()

    def delete_relation_links(self):
        self._ref.deleteRelationLinks()

    def dump(self) -> None:
        self._ref.dump()
