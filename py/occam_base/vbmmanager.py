import occam
from variablelist import VariableList


class VBMManager:
    """
    Wrapper class for VBMManager
    """

    def __init__(self, object_reference=None):
        """
        :param: object_reference: the reference to the VBMManager object returned from the CPP engine
        """
        # Create new reference if one not given
        self._object_reference = object_reference or occam.VBMManager()

    @property
    def variable_list(self):
        """
        Returns a new VariableList object
        """
        return VariableList(self._object_reference.getVariableList())
