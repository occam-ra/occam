from manager import Manager
from model import Model
from occam import VBMManager as VBMManager_cpp
from variable_list import VariableList


class VBMManager(Manager):
    """
    Wrapper class for VBMManager
    """

    def __init__(self, ref=None) -> None:
        """
        :param: ref: Reference to the VBMManager object returned from the CPP engine
        """
        Manager.__init__(self, ref=(ref or VBMManager_cpp()))

    @property
    def variable_list(self) -> VariableList:
        return VariableList(self._ref.getVariableList())

    @property
    def dv_name(self) -> str:
        return self._ref.getDvName()

    def set_alpha_threshold(self, threshold: float) -> None:
        self._ref.setAlphaThreshold(threshold)

    alpha_threshold = property(fset=set_alpha_threshold)

    def set_values_are_functions(self, truth_value: bool) -> None:
        self._ref.setValuesAreFunctions(truth_value)

    values_are_functions = property(fset=set_values_are_functions)

    def use_inverse_notation(self, truth_value: bool) -> None:
        self._ref.setUseInverseNotation(truth_value)

    def make_model(self, model_type: str, make_project: bool) -> Model:
        return Model(self._ref.makeModel(model_type, make_project))

    def set_ddf_method(self, ddf_method: int) -> None:
        self._ref.setDDFMethod(ddf_method)

    ddf_method = property(fset=set_ddf_method)
