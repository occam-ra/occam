import occam
from manager import Manager
from model import Model


class SBMManager(Manager):
    """
    Wrapper class for SBMManager
    """

    def __init__(self, ref=None):
        """
        :param: ref: the reference to the SBMManager object returned from the CPP engine
        """
        Manager.__init__(self, ref=(ref or occam.SBMManager()))

    def make_model(self, model_name: str, make_project: bool) -> Model:
        return Model(self._ref.makeSbModel(model_name, make_project))

    @property
    def test_sample_size(self) -> double:
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
