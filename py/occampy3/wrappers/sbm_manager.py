from manager import Manager
from model import Model
from occam import SBMManager as SBMManager_cpp
from variable_list import VariableList


class SBMManager(Manager):
    """
    Wrapper class for SBMManager
    """

    def __init__(self, ref=None) -> None:
        """
        :param: ref: Reference to the SBMManager object returned from the CPP engine
        """
        Manager.__init__(self, ref=(ref or SBMManager_cpp()))

    def make_model(self, model_type: str, make_project: bool) -> Model:
        return Model(self._ref.makeSbModel(model_type, make_project))

    @property
    def test_sample_size(self) -> float:
        return self._ref.getTestSampleSz()

    @property
    def values_are_functions(self) -> bool:
        return self._ref.getValuesAreFunctions()

    def get_var_count(self) -> int:
        return self._ref.getVarCount()

    @property
    def variable_list(self) -> VariableList:
        return VariableList(self._ref.getVariableList())

    def get_dv(self) -> int:
        return self._ref.getDV()
