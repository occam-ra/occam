class Variable:
    """
    Wrapper class for Variable
    """

    def __init__(self, ref):
        """
        :param: ref: the reference to the Variable object returned from the CPP engine
        """
        self._ref = ref  # type VariableList_cpp

    @property
    def abbrev(self) -> str:
        return self._ref.getAbbrev()
