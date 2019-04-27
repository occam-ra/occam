class VariableList:
    """
    Wrapper class for VariableList
    """

    def __init__(self, ref):
        """
        :param: ref: the reference to the VariableList object returned from the CPP engine
        """
        self._ref = ref  # type VariableList_cpp
