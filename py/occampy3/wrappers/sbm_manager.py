from manager import Manager
from model import Model
from occam import SBMManager as SBMManager_cpp


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
