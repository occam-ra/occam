from enum import Enum
from typing import List, Union


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
        :param: ref: Reference to the Model object returned from the CPP engine
        """
        # Create new reference if one not given
        self.ref = ref

    def __lt__(self, other: 'Model') -> bool:
        return self.name < other.name

    def __eq__(self, other: 'Model') -> bool:
        return self.ref.isEquivalentTo(other.ref)

    @property
    def name(self) -> str:
        return self.get_attribute_value("name")

    @property
    def print_name(self) -> str:
        return self.ref.getPrintName()

    def set_id(self, id_: int) -> None:
        self.ref.setID(id_)

    id_ = property(fset=set_id)

    def make_fit_table(self, model) -> None:
        self.ref.makeFitTable(model)

    def delete_fit_table(self) -> None:
        self.ref.deleteFitTable()

    @property
    def print_name(self) -> str:
        return self.ref.getPrintName()

    @property
    def struct_matrix(self) -> List[int]:
        return self.ref.getStructMatrix()

    def is_equivalent_to(self, other: 'Model') -> bool:
        return self == other

    def set_progenitor(self, progenitor: 'Model') -> None:
        self.ref.setProgenitor(progenitor.ref)

    progenitor = property(fset=set_progenitor)

    def get_attribute_value(self, attribute: str) -> Union[str, float]:
        return self.ref.get(attribute)

    def delete_relation_links(self) -> None:
        self.ref.deleteRelationLinks()

    def dump(self) -> None:
        self.ref.dump()
