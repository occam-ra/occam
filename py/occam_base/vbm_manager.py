import occam3
from variable_list import VariableList
from model import Model, ModelType


class VBMManager:
    """
    Wrapper class for VBMManager
    """

    def __init__(self, ref=None):
        """
        :param: ref: the reference to the VBMManager object returned from the CPP engine
        """
        # Create new reference if one not given
        self._ref = ref or occam3.VBMManager()
        self._model = None

    @property
    def variable_list(self) -> VariableList:
        return VariableList(self._ref.getVariableList())

    def model(self, type_: ModelType = ModelType.DEFAULT, make_project: int = 1) -> Model:
        if type_ is ModelType.TOP:
            model_ref = self._ref.getTopRefModel()
        elif type_ is ModelType.BOTTOM:
            model_ref = self._ref.getBottomRefModel()
        else:
            model_ref = self._ref.makeModel(type_, make_project)

        self._model = Model(model_ref)
        return self._model

    def get_dv_name(self) -> str:
        return self._ref.getDvName()

    def make_model(self, model_name: str, make_project: int) -> None:
        self._model = Model(self._ref.makeModel(model_name, make_project))

    def init_from_command_line(self, data_file: str) -> bool:
        return self._ref.initFromCommandLine(data_file)

    def set_ddf_method(self, ddf_method: int) -> None:
        self._ref.setDDFMethod(ddf_method)

    def compute_l2_statistics(self) -> None:
        self._ref.computeL2Statistics(self._model.get_ref())

    def compute_df_statistics(self) -> None:
        self._ref.computeDFStatistics(self._model.get_ref())

    def compute_dependent_statistics(self) -> None:
        self._ref.computeDependentStatistics(self._model.get_ref())

    def get_option(self, option: str) -> str:
        return self._ref.getOption(option)

    def make_fit_table(self) -> None:
        self._ref.makeFitTable(self._model.get_ref())

    def is_directed(self) -> bool:
        return self._ref.isDirected()

    def get_model(self) -> Model:
        return self._model

    @property
    def search_type(self):
        pass

    @search_type.setter
    def search_type(self, search_type):
        self._ref.setSearchType(search_type)

    def set(self, **kwargs):
        pass
