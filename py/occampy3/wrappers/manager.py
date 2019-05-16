from enum import Enum
from typing import List, Sequence, Tuple, Union

from model import Model, ModelType
from report import Report


class SearchDirection(Enum):
    UP = 0
    DOWN = 1
    DEFAULT = 2


class SearchType(Enum):
    LOOPLESS_UP = 'loopless-up'
    DISJOINT_UP = 'disjoint-up'
    CHAIN_UP = 'chain-up'
    FULL_UP = 'full-up'

    LOOPLESS_DOWN = 'loopless-down'
    DISJOINT_DOWN = 'disjoint-down'
    CHAIN_DOWN = 'chain-down'
    FULL_DOWN = 'full-down'


class SBSearchType(Enum):
    LOOPLESS_UP = 'sb-loopless-up'
    DISJOINT_UP = 'sb-disjoint-up'
    CHAIN_UP = 'sb-chain-up'
    FULL_UP = 'sb-full-up'

    LOOPLESS_DOWN = 'sb-loopless-down'
    DISJOINT_DOWN = 'sb-disjoint-down'
    CHAIN_DOWN = 'sb-chain-down'
    FULL_DOWN = 'sb-full-down'


class SearchFilter(Enum):
    LOOPLESS = 'loopless'
    DISJOINT = 'disjoint'
    CHAIN = 'chain'
    ALL = 'all'


class Manager:
    """
    Wrapper class for Manager
    """

    def __init__(self, ref) -> None:
        """
        :param: ref: Reference to the (VBM,SBM)Manager object returned from the CPP engine
        """
        # Create new reference if one not given
        self._ref = ref
        self._model = None

    @property
    def report(self) -> Report:
        return Report(self._ref.Report())

    def init_from_command_line(self, args: Sequence[str]) -> None:
        self._ref.initFromCommandLine(args)

    def get_option(self, option_name: str) -> str:
        return self._ref.getOption(option_name)

    def get_option_list(self, option_name: str) -> List[str]:
        return self._ref.getOptionList(option_name)

    @property
    def is_directed(self) -> bool:
        return self._ref.isDirected()

    def compute_bp_statistics(self, model: Model) -> None:
        self._ref.computeBPStatistics(model.ref)

    def compute_l2_statistics(self, model: Model) -> None:
        self._ref.computeL2Statistics(model.ref)

    def compute_dfs_statistics(self, model: Model) -> None:
        self._ref.computeDFStatistics(model.ref)

    def compute_dependent_statistics(self, model: Model) -> None:
        self._ref.computeDependentStatistics(model.ref)

    def compute_information_statistics(self, model: Model) -> None:
        self._ref.computeInformationStatistics(model.ref)

    @property
    def top_ref_model(self) -> Model:
        return Model(self._ref.getTopRefModel())

    @property
    def bottom_ref_model(self) -> Model:
        return Model(self._ref.getBottomRefModel())

    def set_search_direction(self, direction: SearchDirection) -> None:
        self._ref.setSearchDirection(direction.value)

    search_direction = property(fset=set_search_direction)

    def set_search_type(self, search_type: Union[SearchType, SBSearchType]) -> None:
        self._ref.setSearchType(search_type.value)

    search_type = property(fset=set_search_type)

    def set_ref_model(self, model) -> None:
        self._ref.setRefModel(model)

    ref_model = property(fset=set_ref_model)

    def get_model_by_search_dir(self, direction: SearchDirection) -> Model:
        return (
            self.top_ref_model
            if direction == SearchDirection.UP
            else self.bottom_ref_model
        )

    def has_test_data(self) -> bool:
        return self._ref.hasTestData()

    def search_one_level(self, model: Model) -> Tuple[Model]:
        model_ref_list = self._ref.searchOneLevel(model.ref)
        return tuple(Model(model_ref) for model_ref in model_ref_list)

    def compare_progenitors(self, model: Model, progen: Model) -> None:
        self._ref.compareProgenitors(model.ref, progen.ref)

    @property
    def mem_usage(self) -> int:
        return self._ref.getMemUsage()

    def delete_model_from_cache(self, model: Model) -> bool:
        return self._ref.deleteModelFromCache(model.ref)

    def compute_percent_correct(self, model: Model) -> None:
        self._ref.computePercentCorrect(model.ref)

    def compute_incremental_alpha(self, model: Model) -> None:
        self._ref.computeIncrementalAlpha(model.ref)

    def make_fit_table(self, model: Model) -> None:
        self._ref.makeFitTable(model.ref)

    def print_options(self, print_html: bool, skip_nominal: bool) -> None:
        self._ref.printOptions(print_html, skip_nominal)

    # TODO: remove and replace with the underlying functionality in the future
    def print_basic_statistics(self) -> None:
        self._ref.printBasicStatistics()

    # TODO: remove and replace with the underlying functionality in the future
    def print_fit_report(self, model: Model) -> None:
        self._ref.printFitReport(model.ref)

    def get_model(self, model_type: ModelType, make_project: bool) -> Model:
        if model_type == ModelType.UP:
            model = self.top_ref_model
        elif model_type == ModelType.BOTTOM:
            model = self.bottom_ref_model
        else:
            model = self.make_model(model_type.value, make_project)
        return model
