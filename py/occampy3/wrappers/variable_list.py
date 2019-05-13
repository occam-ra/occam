from variable import Variable


class VariableList:
    """
    Wrapper class for VariableList
    """

    def __init__(self, ref) -> None:
        """
        :param: ref: the reference to the VariableList object returned from the CPP engine
        """
        self._ref = ref  # type VariableList_cpp

    def __iter__(self) -> 'VariableList':
        self._iter_index = 0
        return self

    def __next__(self) -> Variable:
        """
        Iterate until the highest index reached
        """
        if self._iter_index < self.var_count:
            index = self._iter_index
            self._iter_index += 1
            return Variable(self.get_variable(index))

        raise StopIteration

    @property
    def var_count(self) -> int:
        return self._ref.getVarCount()

    def get_variable(self, index: int):
        return self._ref.getVariable(index)

    def is_directed(self) -> bool:
        return self._ref.isDirected()
