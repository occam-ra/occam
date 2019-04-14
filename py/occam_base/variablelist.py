class VariableList:
    """
    Wrapper class for VariableList
    """
    _object_reference = None    # type VariableList_cpp

    def __init__(self, object_reference):
        """
        :param: object_reference: the reference to the VariableList object returned from the CPP engine
        """

        self._object_reference = object_reference
