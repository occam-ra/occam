import occam3
from manager import Manager
from variable_list import VariableList


class VBMManager(Manager):
    """
    Wrapper class for VBMManager
    """

    def __init__(self, ref=None):
        """
        :param: ref: the reference to the VBMManager object returned from the CPP engine
        """
        Manager.__init__(self, ref=(ref or occam3.VBMManager()))

    @property
    def variable_list(self):
        return VariableList(self._ref.getVariableList())

    def set_alpha_threshold(self, threshold: int) -> None:
        self._ref.setAlphaThreshold(threshold)

    def values_are_functions(self, truth_value: bool) -> None:
        self._ref.setValuesAreFunctions(truth_value)

    def use_inverse_notation(self, truth_value: bool) -> None:
        self._ref.setUseInverseNotation(truth_value)
