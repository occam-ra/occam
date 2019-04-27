import occam


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
        self.ref.makeFitTable(model)

    @fit_table.deleter
    def fit_table(self):
        self.ref.deleteFitTable()

    def set(self, **kwargs):
        pass
