import occam
from manager import Manager


class VBMManager(Manager):
    """
    Wrapper class for VBMManager
    """

    def __init__(self, ref=None):
        """
        :param: ref: the reference to the VBMManager object returned from the CPP engine
        """
        super(VBMManager).__init__()
        # Create new reference if one not given
        self._ref = ref or occam.VBMManager()
