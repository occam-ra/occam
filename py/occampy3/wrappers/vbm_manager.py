import occam
from manager import Manager
from variable_list import VariableList
from model import Model


class VBMManager(Manager):
    """
    Wrapper class for VBMManager
    """

    def __init__(self, ref=None):
        """
        :param: ref: the reference to the VBMManager object returned from the CPP engine
        """
        Manager.__init__(self, ref=(ref or occam.VBMManager()))

    @property
    def variable_list(self):
        return VariableList(self._ref.getVariableList())

    @property
    def dv_name(self) -> str:
        return self._ref.getDvName()

    def set_alpha_threshold(self, threshold: float) -> None:
        self._ref.setAlphaThreshold(threshold)

    def values_are_functions(self, truth_value: bool) -> None:
        self._ref.setValuesAreFunctions(truth_value)

    def use_inverse_notation(self, truth_value: bool) -> None:
        self._ref.setUseInverseNotation(truth_value)

    def make_model(self, model_name: str, make_project: bool) -> Model:
        return Model(self._ref.makeModel(model_name, make_project))

    def set_ddf_method(self, ddf_method: int) -> None:
        self._ref.setDDFMethod(ddf_method)
