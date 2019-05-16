from enum import Enum
from typing import Dict

from model import Model
from variable_list import VariableList


class SeparatorType(Enum):
    TAB = 1
    COMMA = 2
    SPACE = 3
    HTML = 4


class SortDirection(Enum):
    ASCENDING = "ascending"
    DESCENDING = "descending"


class ReportSortName(Enum):
    AIC = "aic"
    ALPHA = "alpha"
    BIC = "bic"
    BP_ALPHA = "bp_alpha"
    BP_INFORMATION = "bp_information"
    BPT = "bp_t"
    INFORMATION = "information"
    PCT_CORRECT_DATA = "pct_correct_data"


class Report:
    """
    Wrapper class for Report
    """

    def __init__(self, ref=None) -> None:
        """
        :param ref: Reference to the Report object returned from the CPP engine
        """
        self._ref = ref  # type Report_cpp

    @property
    def variable_list(self) -> VariableList:
        return VariableList(self._ref.variableList())

    @property
    def dv_name(self) -> str:
        return self._ref.dvName()

    def set_separator(self, separator: SeparatorType) -> None:
        self._ref.setSeparator(separator.value)

    separator = property(fset=set_separator)

    def add_model(self, model: Model) -> None:
        self._ref.addModel(model.ref)

    def set_default_fit_model(self, model: Model) -> None:
        self._ref.setDefaultFitModel(model.ref)

    default_fit_model = property(fset=set_default_fit_model)

    def print_conditional_dv(self, model: Model, calc_expected_dv: bool, classifier_target: str) -> None:
        self._ref.printConditional_DV(
            model.ref, calc_expected_dv, classifier_target
        )

    def print_residuals(self, model: Model, skip_trained_model_table: bool, skip_ivi_tables: bool) -> None:
        self._ref.printResiduals(
            model.ref, skip_trained_model_table, skip_ivi_tables
        )

    def set_attributes(self, attributes: str) -> None:
        self._ref.setAttributes(attributes)

    def sort(self, sort_name: str, sort_direction: SortDirection) -> None:
        self._ref.sort(sort_name, sort_direction.value)

    def write_report(self, stream: str) -> None:
        self._ref.writeReport(stream)

    def print_report(self) -> None:
        self._ref.printReport()

    def best_model_data(self) -> Dict:
        return self._ref.bestModelData()
