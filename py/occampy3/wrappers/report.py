from enum import Enum
from model import Model


class SeparatorType(Enum):
    TAB = 1
    COMMA = 2
    SPACE = 3
    HTML = 4


class Report:
    """
    Wrapper class for Report
    """

    def __init__(self, ref):
        """
        :param: ref: the reference to the Report object returned from the CPP engine
        """
        self._ref = ref  # type Report_cpp

    def set_separator(self, separator: SeparatorType) -> None:
        self._ref.setSeparator(separator.value)

    def add_model(self, model: Model) -> None:
        self._ref.addModel(model.ref)

    def set_default_fit_model(self, model: Model) -> None:
        self._ref.setDefaultFitModel(model.ref)

    def print_conditional_dv(self, model: Model, calc_expected_dv: bool, classifier_target: str) -> None:
        self._ref.printConditional_DV(model.ref, calc_expected_dv, classifier_target)

    def print_residuals(self, model: Model, skip_trained_model_table: bool, skip_ivi_tables: bool) -> None:
        self._ref.printResiduals(model.ref, skip_trained_model_table, skip_ivi_tables)