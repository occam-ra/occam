from variable_list import VariableList


class Manager:
    """
    Wrapper class for Manager
    """

    def __init__(self):
        """
        :param: ref: the reference to the Manager object returned from the CPP engine
        """
        # Create new reference if one not given
        self._model = None

    @property
    def variable_list(self):
        return VariableList(self._ref.getVariableList())

    @property
    def model(self, type_='default', make_project=1):
        if type_ == 'top':
            model = self._ref.getTopRefModel()
        elif type_ == 'bottom':
            model = self._ref.getBottomRefModel()
        else:
            model = self._ref.makeModel(type_, make_project)
        self._model = model
        return model

    @property
    def search_type(self):
        pass

    @search_type.setter
    def search_type(self, search_type):
        self._ref.setSearchType(search_type)

    def set(self, **kwargs):
        pass
