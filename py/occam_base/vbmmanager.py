import occam
from variablelist import VariableList

class VBMManager:
    """
    Wrapper class for VBMManager
    """
    _object_reference = None     # type VBMManager_cpp

    def __init__(self, object_reference = None):
        """
        :param: object_reference: the reference to the VBMManager object returned from the CPP engine
        """

        # Create new reference if one not given
        if object_reference is None:    
            self._object_reference = occam.VBMManager()

        else:
            self._object_reference = object_reference

    def get_variable_list(self):
        """
        Returns a new VariableList object
        """
        return VariableList(self._object_reference.getVariableList())
