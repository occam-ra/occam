from enum import Enum


class ModelType(Enum):
    TOP = 'top'
    BOTTOM = 'bottom'
    DEFAULT = 'default'


class Model:
    """
    Wrapper class for Model
    """

    def __init__(self, ref=None):
        """
        :param: ref: the reference to the Model object returned from the CPP engine
        """
        # Create new reference if one not given
        self._ref = ref
        self._id = 0

    @property
    def id_(self):
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

    @property
    def print_name(self):
        return self._ref.getPrintName()

    def get_struct_matrix(self):
        return self._ref.getStructMatrix()

    @property
    def ref(self):
        return self._ref

    def is_equivalent_to(self):
        return self._ref.isEquivalentTo()

    def get_progenitor(self):
        return self._ref.getProgenitor()

    def set_progenitor(self, progenitor):
        self._ref.setProgenitor(progenitor.ref)

    def delete_relation_links(self):
        self._ref.deleteRelationLinks()

    def dump(self):
        self._ref.dump()
