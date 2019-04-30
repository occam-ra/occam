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
