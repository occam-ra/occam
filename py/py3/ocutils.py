# coding=utf-8
# Copyright © 1990 The Portland State University OCCAM Project Team
# [This program is licensed under the GPL version 3 or later.]
# Please see the file LICENSE in the source
# distribution of this software for license terms.

# coding=utf8
import heapq
import re
import sys
import time
from enum import Enum
from typing import Dict, List, Sequence, Tuple, Union

import ocGraph
from model import Model, ModelType
from report import ReportSortName, SeparatorType, SortDirection
from sbm_manager import SBMManager
from vbm_manager import VBMManager
from wrappers.manager import (
    SBSearchType,
    SearchDirection,
    SearchFilter,
    SearchType,
)

max_memory_to_use = 8 * 2 ** 30


class Action(Enum):
    FIT = 'fit'
    SEARCH = 'search'
    SBSEARCH = 'SBsearch'
    SBFIT = 'SBfit'


class OCUtils:
    def __init__(self, man: str = "VB") -> None:
        if man == "VB":
            self._manager = VBMManager()
        else:
            self._manager = SBMManager()
        self._action = ""
        self._alpha_threshold = 0.05
        self._bp_statistics = 0
        self._calc_expected_dv = False
        self._data_file = ""
        self._ddf_method = 0
        self._default_fit_model = ""
        self._fit_classifier_target = ""
        self._fit_models = []
        self._full_var_names = False
        self._generate_gephi = False
        self._generate_graph = False
        self._graph_font_size = 12
        self._graph_height = 500
        self._graph_hideDV = False
        self._graph_node_size = 36
        self._graph_width = 500
        self._hide_intermediate_output = False
        self._hide_isolated = True
        self._HTMLFormat = False
        self._incremental_alpha = 0
        self._layout_style = None
        self._next_id = 0
        self._no_ipf = 0
        self._percent_correct = 0
        self._ref_model = ModelType.DEFAULT
        self._report = self._manager.report
        self._report.separator = (
            SeparatorType.SPACE
        )  # align columns using spaces
        self._report_file = ""
        self._report_sort_name = ""
        self._search_filter = SearchFilter.LOOPLESS
        self._search_levels = 7
        self._search_sort_dir = SortDirection.ASCENDING
        self._search_width = 3
        self._skip_ivi_tables = True
        self._skip_nominal = False
        self._skip_trained_model_table = True
        self._sort_dir = SortDirection.ASCENDING
        self.start_model = ModelType.DEFAULT
        self._total_gen = 0
        self._total_kept = 0
        self._use_inverse_notation = False
        self._values_are_functions = False
        self.graphs = {}
        self.search_dir = SearchDirection.DEFAULT
        self.sort_name = "ddf"
        # self._show_edge_weights = True
        # self._weight_fn = "Mutual Information"

    # -- Read command line args and process input file
    def init_from_command_line(self, argv: Sequence[str]) -> None:
        self._manager.init_from_command_line(args=argv)
        self.occam2_settings()

    # -- Set up report variables
    def set_report_variables(self, report_attributes: str) -> None:
        # if the data uses function values, we want to skip the attributes that require a sample size
        option = self._manager.get_option("function-values")
        if option != "" or self._values_are_functions != 0:
            report_attributes = re.sub(
                r",\s(?:incr_)?alpha|lr|[ab]ic", '', report_attributes
            )
        self._report.set_attributes(report_attributes)
        if re.search('bp_t', report_attributes):
            self._bp_statistics = 1
        if re.search('pct_correct', report_attributes):
            self._percent_correct = 1
        if re.search('incr_alpha', report_attributes):
            self._incremental_alpha = 1

    def set_report_separator(self, format_: SeparatorType) -> None:
        # occam.setHTMLMode(format_ == OCUtils.HTML_FORMAT)
        self._report.separator = format_
        # self._HTMLFormat = format_ == OCUtils.HTML_FORMAT

    def set_fit_classifier_target(self, target: str) -> None:
        self._fit_classifier_target = target

    def set_skip_trained_model_table(self, b: int) -> None:
        self._skip_trained_model_table = b

    def set_skip_ivi_tables(self, b) -> None:
        self._skip_ivi_tables = b

    def set_skip_nominal(self, use_flag: int) -> None:
        self._skip_nominal = use_flag

    def set_use_inverse_notation(self, use_flag: int) -> None:
        if use_flag != 1:
            use_flag = 0
        self._use_inverse_notation = use_flag

    def set_values_are_functions(self, use_flag: int) -> None:
        if use_flag != 1:
            use_flag = 0
        self._values_are_functions = use_flag

    # -- Set control attributes
    def set_ddf_method(self, ddf_method: int) -> None:
        if ddf_method != 1:
            ddf_method = 0
        self._ddf_method = ddf_method

    def set_sort_dir(self, sort_dir: Union[SortDirection, str]) -> None:
        self._sort_dir = SortDirection(sort_dir)

    def set_search_sort_dir(self, sort_dir: Union[SortDirection, str]) -> None:
        if sort_dir == "":
            sort_dir = SortDirection.DESCENDING
        sort_dir = SortDirection(sort_dir)
        if (
            sort_dir != SortDirection.ASCENDING
            and sort_dir != SortDirection.DESCENDING
        ):
            raise AttributeError("set_search_sort_dir")
        self._search_sort_dir = sort_dir

    def set_search_width(self, search_width) -> None:
        width = int(round(float(search_width)))
        if width <= 0:
            width = 1
        self._search_width = width

    def set_search_levels(self, search_levels) -> None:
        levels = int(round(float(search_levels)))
        levels = max(0, levels)  # zero is OK here
        self._search_levels = levels

    def set_report_sort_name(
        self, sort_name: Union[ReportSortName, str]
    ) -> None:
        self._report_sort_name = ReportSortName(sort_name)

    def set_search_filter(
        self, search_filter: Union[SearchFilter, str]
    ) -> None:
        self._search_filter = SearchFilter(search_filter)

    def set_alpha_threshold(self, alpha_threshold: str) -> None:
        self._alpha_threshold = float(alpha_threshold)

    def set_start_model(self, start_model: Union[ModelType, str]) -> None:
        if start_model not in [*ModelType, ""]:
            self.check_model_name(start_model)
        self.start_model = start_model

    def set_fit_model(self, fit_model: str) -> None:
        self._fit_models = [fit_model]

    def set_report_file(self, report_file) -> None:
        self._report_file = report_file

    def set_action(self, action: Union[Action, str]) -> None:
        self._action = Action(action)

    def set_data_file(self, data_file: str) -> None:
        self._data_file = data_file

    def set_calc_expected_dv(self, calc_expected_dv: int) -> None:
        self._calc_expected_dv = calc_expected_dv

    def set_default_fit_model(self, model: int) -> None:
        self._default_fit_model = model

    def set_no_ipf(self, state: int) -> None:
        self._no_ipf = state

    @property
    def is_directed(self) -> bool:
        return self._manager.is_directed

    def has_test_data(self) -> bool:
        return self._manager.has_test_data()

    # -- Search operations
    # compare function for sorting models. The python list sort function uses this
    # the name of the attribute to sort on is given above, as well as ascending or descending
    def _compare_models(self, m1, m2) -> int:
        result = 0
        a1 = m1.get(self.sort_name)
        a2 = m2.get(self.sort_name)
        if a1 > a2:
            result = -1
        if a1 < a2:
            result = 1
        if self._search_sort_dir == SortDirection.ASCENDING:
            result = -result
        return result

    # this function decides which statistic to computed, based
    # on how search is sorting the models. We want to avoid any
    # extra expensive computations
    def compute_sort_statistic(self, model: Model) -> None:
        if self.sort_name in {"h", "information", "unexplained", "alg_t"}:
            self._manager.compute_information_statistics(model)
        elif self.sort_name == "df" or self.sort_name == "ddf":
            self._manager.compute_dfs_statistics(model)
        elif self.sort_name in {"bp_t", "bp_information", "bp_alpha"}:
            self._manager.compute_bp_statistics(model)
        elif self.sort_name == "pct_correct_data":
            self._manager.compute_percent_correct(model)
        # anything else, just compute everything we might need
        else:
            self._manager.compute_l2_statistics(model)
            self._manager.compute_dependent_statistics(model)

    # this function generates the parents/children of the given model, and for
    # any which haven't been seen before puts them into the new_model list
    # this function also computes the LR statistics (H, LR, DF, etc.) as well
    # as the dependent statistics (dH, %dH, etc.)
    def process_model(
        self,
        level: int,
        new_models_heap: List[Tuple[Union[str, float], Union[str, float], Model]],
        model: Model
    ) -> int:
        add_count = 0
        generated_models = self._manager.search_one_level(model)
        for new_model in generated_models:
            if new_model.get_attribute_value("processed") <= 0.0:
                new_model.processed = 1.0
                new_model.level = level  # Unused?
                new_model.progenitor = model
                self.compute_sort_statistic(new_model)
                # need a fix here (or somewhere) to check for (and remove) models that have the same DF as the progenitor
                # decorate model with a key for sorting, & push onto heap
                key = new_model.get_attribute_value(self.sort_name)
                if self._search_sort_dir == SortDirection.DESCENDING:
                    key = -key
                heapq.heappush(
                    new_models_heap,
                    ([key, new_model.get_attribute_value("name")], new_model),
                )  # appending the model name makes sort alphabet-consistent
                add_count += 1
            else:
                if self._incremental_alpha:
                    # this model has been made already, but this progenitor might lead to a better Incr.Alpha
                    # so we ask the manager to check on that, and save the best progenitor
                    self._manager.compare_progenitors(new_model, model)
        return add_count

    # This function processes models from one level, and return models for the next level.
    def process_level(
        self, level: int, old_models: List[Model], clear_cache_flag: bool
    ) -> List[Model]:
        # start a new heap
        new_models_heap = []
        full_count = 0
        for model in old_models:
            full_count += self.process_model(level, new_models_heap, model)
        # if search_width < heapsize, pop off search_width and add to best_models
        best_models = []
        while len(new_models_heap) > 0:
            # make sure that we're adding unique models to the list (mostly for state-based)
            key, candidate = heapq.heappop(new_models_heap)
            # if len(best_models) < self._search_width:  # or key[0] == last_key[0]:      # comparing keys allows us to select more than <width> models,
            if len(best_models) < self._search_width and not any(
                {n == candidate for n in best_models}
            ):  # in the case of ties
                best_models.append(candidate)
            else:
                break
        trunc_count = len(best_models)
        self._total_gen = full_count + self._total_gen
        self._total_kept = trunc_count + self._total_kept
        mem_used = self._manager.mem_usage
        if not self._hide_intermediate_output:
            print(
                f'{full_count} new models, {trunc_count} kept; '
                f'{self._total_gen + 1} total models, '
                f'{self._total_kept + 1} total kept; '
                f'{mem_used / 1024} kb memory used; ',
                end=' ',
            )
        sys.stdout.flush()
        if clear_cache_flag:
            for item in new_models_heap:
                self._manager.delete_model_from_cache(item[1])
        return best_models

    # This function returns the name of the search strategy to use based on
    # the search_mode and loopless settings above
    def search_type(self, sb=False) -> Union[SearchType, SBSearchType]:
        search_type = SBSearchType if sb else SearchType
        if self.search_dir == SearchDirection.UP:
            return {
                SearchFilter.LOOPLESS: search_type.LOOPLESS_UP,
                SearchFilter.DISJOINT: search_type.DISJOINT_UP,
                SearchFilter.CHAIN: search_type.CHAIN_UP,
            }.get(self._search_filter, search_type.FULL_UP)
        else:
            return {
                SearchFilter.LOOPLESS: search_type.LOOPLESS_DOWN,
                SearchFilter.DISJOINT: search_type.DISJOINT_DOWN,
                SearchFilter.CHAIN: search_type.CHAIN_DOWN,
            }.get(self._search_filter, search_type.FULL_DOWN)

    def do_search(self, print_options: int) -> None:
        if self._manager.is_directed and (
            self.search_dir == SearchDirection.DOWN
            and self._search_filter == SearchFilter.CHAIN
        ):
            print('ERROR: Directed Down Chain Search not yet implemented.')
            raise sys.exit()
        else:
            if (
                self.search_dir == SearchDirection.UP
                and self._search_filter == SearchFilter.CHAIN
            ):
                print('ERROR: Neutral Down Chain Search not yet implemented.')
                raise sys.exit()

        if self.start_model == "":
            self.start_model = ModelType.DEFAULT
        if self.search_dir == SearchDirection.DEFAULT:
            self.search_dir = SearchDirection.UP
        # set start model. For chain search, ignore any specific starting model
        # otherwise, if not set, set the start model based on search direction
        if (
            self._search_filter == SearchFilter.CHAIN
            or self.start_model == ModelType.DEFAULT
        ) and self.search_dir == SearchDirection.DOWN:
            self.start_model = ModelType.TOP
        elif (
            self._search_filter == SearchFilter.CHAIN
            or self.start_model == ModelType.DEFAULT
        ) and self.search_dir == SearchDirection.UP:
            self.start_model = ModelType.BOTTOM
        start = self._manager.get_model(self.start_model, True)
        self._manager.ref_model = self._ref_model
        self._manager.use_inverse_notation(self._use_inverse_notation)
        self._manager.values_are_functions(self._values_are_functions)
        self._manager.alpha_threshold = self._alpha_threshold
        if self.search_dir == SearchDirection.DOWN:
            self._manager.search_direction = SearchDirection.DOWN
        else:
            self._manager.search_direction = SearchDirection.UP
        if print_options:
            self.print_options(1)
        self._manager.print_basic_statistics()
        self._manager.compute_l2_statistics(start)
        self._manager.compute_dependent_statistics(start)
        if self._bp_statistics:
            self._manager.compute_bp_statistics(start)
        if self._percent_correct and self._manager.is_directed:
            self._manager.compute_percent_correct(start)
        if self._incremental_alpha:
            self._manager.compute_incremental_alpha(start)
        start.level = 0  # Unused?
        self._report.add_model(start)
        self._next_id = 1
        start.id_ = self._next_id
        start.progenitor = start
        old_models = [start]
        try:
            self._manager.search_type = self.search_type()
        except Exception:
            print(f"ERROR: UNDEFINED SEARCH FILTER {self._search_filter}")
            return
        # process each level, up to the number of levels indicated. Each of the best models
        # is added to the report generator for later output
        self.newl('<pre>')
        print("Searching levels:")
        start_time = time.time()
        last_time = start_time
        for i in range(1, self._search_levels + 1):
            if self._manager.mem_usage > max_memory_to_use:
                print("Memory limit exceeded: stopping search")
                break
            print(i, ':', end=' ')  # progress indicator
            new_models = self.process_level(
                i, old_models, i != self._search_levels
            )
            current_time = time.time()
            print(
                f'{current_time - last_time:.1f} seconds, '
                f'{current_time - start_time:.1f} total'
            )
            sys.stdout.flush()
            last_time = current_time
            for model in new_models:
                # Make sure all statistics are calculated. This won't do anything if we did it already.
                if not self._no_ipf:
                    self._manager.compute_l2_statistics(model)
                    self._manager.compute_dependent_statistics(model)
                if self._bp_statistics:
                    self._manager.compute_bp_statistics(model)
                if self._percent_correct:
                    self._manager.compute_percent_correct(model)
                if self._incremental_alpha:
                    self._manager.compute_incremental_alpha(model)
                self._next_id += 1
                model.id_ = self._next_id
                # model.deleteFitTable()  #recover fit table memory
                self._report.add_model(model)
            old_models = new_models
            # if the list is empty, stop. Also, only do one step for chain search
            if (
                self._search_filter == SearchFilter.CHAIN
                or len(old_models) == 0
            ):
                break
        self.newl('</pre><br>')
        if not self._HTMLFormat:
            print()

    def do_sb_search(self, print_options: int) -> None:
        if self.start_model == "":
            self.start_model = ModelType.DEFAULT
        if self.search_dir == SearchDirection.DEFAULT:
            self.search_dir = SearchDirection.UP
        if (
            self._search_filter == SearchFilter.CHAIN
            or self.start_model == ModelType.DEFAULT
        ) and self.search_dir == SearchDirection.DOWN:
            self.start_model = ModelType.TOP
        elif (
            self._search_filter == SearchFilter.CHAIN
            or self.start_model == ModelType.DEFAULT
        ) and self.search_dir == SearchDirection.UP:
            self.start_model = ModelType.BOTTOM
        start = self._manager.get_model(self.start_model, True)
        self._manager.ref_model = self._ref_model
        if self.search_dir == SearchDirection.DOWN:
            self._manager.search_direction = SearchDirection.DOWN
        else:
            self._manager.search_direction = SearchDirection.UP
        if print_options:
            self.print_options(1)
        self._manager.print_basic_statistics()
        self._manager.compute_l2_statistics(start)
        self._manager.compute_dependent_statistics(start)
        if self._percent_correct and self._manager.is_directed:
            self._manager.compute_percent_correct(start)
        if self._incremental_alpha:
            self._manager.compute_incremental_alpha(start)
        start.level = 0  # Unused?
        self._report.add_model(start)
        self._next_id = 1
        start.id_ = self._next_id
        start.progenitor = start
        old_models = [start]
        try:
            self._manager.search_type = self.search_type(sb=True)
        except Exception:
            print(f"ERROR: UNDEFINED SEARCH FILTER {self._search_filter}")
            return
        self.newl('<pre>')
        print("Searching levels:")
        start_time = time.time()
        last_time = start_time
        for i in range(1, self._search_levels + 1):
            if self._manager.mem_usage > max_memory_to_use:
                print("Memory limit exceeded: stopping search")
                break
            print(i, ':', end=' ')  # progress indicator
            new_models = self.process_level(
                i, old_models, i != self._search_levels
            )
            current_time = time.time()
            print(
                f'{current_time - last_time:.1f} seconds, '
                f'{current_time - start_time:.1f} total'
            )
            last_time = current_time
            for model in new_models:
                # Make sure all statistics are calculated. This won't do anything if we did it already.
                if not self._no_ipf:
                    self._manager.compute_l2_statistics(model)
                    self._manager.compute_dependent_statistics(model)
                if self._bp_statistics:
                    self._manager.compute_bp_statistics(model)
                if self._percent_correct:
                    self._manager.compute_percent_correct(model)
                if self._incremental_alpha:
                    self._manager.compute_incremental_alpha(model)
                self._next_id += 1
                model.id_ = self._next_id
                model.delete_fit_table()  # recover fit table memory
                self._report.add_model(model)
            old_models = new_models
            # if the list is empty, stop. Also, only do one step for chain search
            if (
                self._search_filter == SearchFilter.CHAIN
                or len(old_models) == 0
            ):
                break
        self.newl('</pre><br>')
        if not self._HTMLFormat:
            print()

    def print_search_report(self) -> None:
        # sort the report as requested, and print it.
        if self._report_sort_name != "":
            sort_name = self._report_sort_name.value
        else:
            sort_name = self.sort_name
        self._report.sort(sort_name, self._sort_dir)
        if self._report_file != "":
            self._report.write_report(self._report_file)
        else:
            self._report.print_report()

        # -- self._manager.dumpRelations()

    def print_search_graphs(self) -> None:

        if not (self._generate_graph or self._generate_gephi):
            return

        # in HTML mode, note that the graphs are being printed.
        self.newl('<hr>')

        # Get the varlist (used for all graphs)

        # Graphs for each kind of best model:
        # Generate the graph (but don't print anything yet).
        # BIC [1 or more]

        # AIC [1 or more]

        # Incr Alpha [0 or more]

        # For each of the graphs (and headers) above,
        # if HTML mode, print out a brief note and graph/gephi (if enabled)

    def newl(self, html: str = "<br>") -> None:
        if self._HTMLFormat:
            print(html)

    @staticmethod
    def split_caps(s) -> List[str]:
        return re.findall('[A-Z][^A-Z]*', s)

    def split_model(self, model_name: str) -> List[List[str]]:
        comps = model_name.split(":")
        model = [
            [s]
            if (s == "IV" if self.is_directed else s == "IVI")
            else self.split_caps(s)
            for s in comps
        ]
        return model

    def check_model_name(self, model_name: str) -> None:
        varlist = [v.abbrev for v in self._manager.variable_list]
        model = self.split_model(model_name)
        is_directed = self.is_directed
        have_ivs = False
        saw_maybe_wrong_iv = False

        # IV can be present if directed system; IVI otherwise
        if is_directed:
            if ["I", "V", "I"] in model:
                saw_maybe_wrong_iv = True
            if ["IV"] in model:
                have_ivs = True
        else:
            if ["I", "V"] in model:
                saw_maybe_wrong_iv = True
            if ["IVI"] in model:
                have_ivs = True

        # all variables in varlist are in model (possibly as IV or IVI)
        modelvars = [var for rel in model for var in rel]

        varset = set(varlist)
        modset = set(modelvars)
        if is_directed:
            modset.discard("IV")
        else:
            modset.discard("IVI")

        if not (have_ivs or varset.issubset(modset)):
            self.newl()
            print(
                f"\nERROR: Not all declared variables are present in the "
                f"model, '{model_name}'."
            )
            self.newl()
            if saw_maybe_wrong_iv:
                print(
                    f"\n_did you mean '{'IV' if is_directed else 'IVI'}' "
                    f"instead of '{'IVI' if is_directed else 'IV'}"
                )
            else:
                print(
                    f"\n Did you forget the {'IV' if is_directed else 'IVI'} component?"
                )
            self.newl()
            print("\n Not in model: ")
            print(", ".join([f"'{i}'" for i in varset.difference(modset)]))
            sys.exit(1)

        # all variables in model are in varlist
        if not modset.issubset(varset):
            self.newl()
            print(
                f"\nERROR: Not all variables in the model '{model_name}' are "
                f"declared in the variable list."
            )
            self.newl()
            diffset = modset.difference(varset)
            if saw_maybe_wrong_iv or diffset == {"I", "V"}:
                print(
                    f"\n_did you mean '{'IV' if is_directed else 'IVI'}' "
                    f"instead of '{'IVI' if is_directed else 'IV'}'?"
                )
            else:
                print("\n Not declared: ")
                print(", ".join([f"'{i}'" for i in diffset]))

            sys.exit(1)

        # dv must be in all components (except IV) if directed
        if is_directed:
            dv = self._manager.dv_name
            for rel in model:
                if not (rel == ["IVI"] or rel == ["IV"]) and dv not in rel:
                    self.newl()
                    print(
                        f"\nERROR: In the model '{model_name}', model component "
                        f"'{''.join(rel)}' is missing the DV, '{dv}'."
                    )
                    sys.exit(1)

    def print_graph(self, model_name: str, only_gfx: bool) -> None:
        if only_gfx and not self._generate_gephi:
            self._generate_graph = True
        if (self._generate_graph or self._generate_gephi) and (
            self._hide_isolated and (model_name == "IVI" or model_name == "IV")
        ):
            msg = "Note: no "
            if self._generate_graph:
                msg += "hypergraph image "
            if self._generate_graph and self._generate_gephi:
                msg += "or "
            if self._generate_gephi:
                msg += "Gephi input "
            msg += (
                " was generated, since the model contains only "
                f"{model_name} components, which were requested to be "
                "hidden in the graph"
            )

            self.newl()
            print(msg)
            self.newl()

        else:
            self.maybe_print_graph_svg(model_name, True)
            self.maybe_print_graph_gephi(model_name, True)
        print("\n")

    def do_fit(self, print_options: int, only_gfx: bool) -> None:
        # self._manager.values_are_functions = self._values_are_functions

        if print_options and not only_gfx:
            self.print_options(0)

        if not only_gfx:
            self._manager.print_basic_statistics()

        for model_name in self._fit_models:
            self.check_model_name(model_name)
            self._manager.ref_model = self._ref_model
            model = self._manager.make_model(
                model_name=model_name, make_project=True
            )

            if only_gfx:
                self.print_graph(model_name, only_gfx)
                continue

            self.do_all_computations(model)

            if self._default_fit_model != "":
                try:
                    default_model = self._manager.make_model(
                        model_name=self._default_fit_model, make_project=True
                    )
                except Exception:
                    print(
                        f"\nERROR: Unable to create model {self._default_fit_model}"
                    )
                    sys.exit(0)
                self._report.default_fit_model = default_model
            self._report.print_conditional_dv(
                model=model,
                calc_expected_dv=self._calc_expected_dv,
                classifier_target=self._fit_classifier_target,
            )

            self.print_graph(model_name, only_gfx)

    def maybe_print_graph_svg(self, model, header) -> None:

        if self._generate_graph:
            self.generate_graph(model)
            if self._HTMLFormat:
                if header:
                    print(
                        f"Hypergraph model visualization for the Model {model}"
                        f" (using the {self._layout_style} layout algorithm)<br>"
                    )
                ocGraph.print_svg(
                    self.graphs[model],
                    self._layout_style,
                    self._graph_width,
                    self._graph_height,
                    self._graph_font_size,
                    self._graph_node_size,
                )
                print("<hr>")

    def maybe_print_graph_gephi(self, model, header) -> None:

        if self._generate_gephi:
            self.generate_graph(model)

            if self._HTMLFormat:
                if header:
                    print(
                        f"Hypergraph model Gephi input for the Model {model}<br>"
                    )
                print(ocGraph.print_gephi(self.graphs[model]))
                print("<hr>")

    def generate_graph(self, model) -> None:
        if model not in self.graphs:
            self.graphs[model] = ocGraph.generate(
                model,
                varlist=self._report.variable_list,
                hide_iv=self._hide_isolated,
                hide_dv=self._graph_hideDV,
                dv_name=self._report.dv_name if self.is_directed else "",
                full_var_names=self._full_var_names,
                all_higher_order=self._layout_style == "bipartite",
            )

    def set_gfx(
        self,
        use_gfx,
        layout=None,
        gephi=False,
        hide_iv=True,
        hide_dv=True,
        full_var_names=False,
        width=640,
        height=480,
        font_size=12,
        node_size=24,
    ) -> None:
        self._generate_graph = use_gfx
        self._generate_gephi = gephi
        self._layout_style = layout
        self._hide_isolated = hide_iv
        self._graph_hideDV = hide_dv
        self._full_var_names = full_var_names
        self._graph_width = width
        self._graph_height = height
        self._graph_font_size = font_size
        self._graph_node_size = node_size

    def do_all_computations(self, model: Model) -> None:
        self._manager.compute_l2_statistics(model)
        self._manager.compute_dfs_statistics(model)
        self._manager.compute_dependent_statistics(model)
        self._report.add_model(model)
        self._manager.print_fit_report(model)
        self._manager.make_fit_table(model)
        self._report.print_residuals(
            model=model,
            skip_trained_model_table=self._skip_trained_model_table,
            skip_ivi_tables=self._skip_ivi_tables,
        )

    def do_sb_fit(self, print_options: int) -> None:
        # self._manager.values_are_functions = self._values_are_functions
        if print_options:
            self.print_options(0)
        self._manager.print_basic_statistics()
        for model_name in self._fit_models:
            self._manager.ref_model = self._ref_model
            model = self._manager.make_model(model_name, True)
            self.do_all_computations(model)
            if self._default_fit_model != "":
                try:
                    default_model = self._manager.make_model(
                        self._default_fit_model, True
                    )
                except Exception:
                    print(
                        "\nERROR: Unable to create model "
                        + self._default_fit_model
                    )
                    sys.exit(0)
                self._report.default_fit_model = default_model
            self._report.print_conditional_dv(
                model, self._calc_expected_dv, self._fit_classifier_target
            )

            print("\n")

    def occam2_settings(self) -> None:
        action = self._manager.get_option("action")
        if action != "":
            self._action = Action(action)
        search_levels = self._manager.get_option("search-levels")
        if search_levels != "":
            self._search_levels = int(float(search_levels))
        search_width = self._manager.get_option("optimize-search-width")
        if search_width != "":
            self._search_width = int(float(search_width))
        ref_model = self._manager.get_option("reference-model")
        if ref_model != "":
            self._ref_model = ref_model
        search_dir = self._manager.get_option("search-direction")
        if search_dir != "":
            self.search_dir = search_dir
        models = self._manager.get_option_list("short-model")
        # for search, only one specified model allowed
        if len(models) > 0:
            self.start_model = ModelType(models[0])
            self._fit_models = [ModelType(model) for model in models]

    def do_action(self, print_options: int, only_gfx: bool = False) -> None:
        # set reporting variables based on ref model
        if self._ref_model == ModelType.DEFAULT:
            if self.search_dir == SearchDirection.DOWN:
                self._ref_model = ModelType.TOP
            else:
                self._ref_model = ModelType.BOTTOM

        if self._action == Action.SEARCH:
            self._manager.ddf_method = self._ddf_method
            self.do_search(print_options)
            self.print_search_report()
        elif self._action == Action.FIT:
            self._manager.ddf_method = self._ddf_method
            self.do_fit(print_options, only_gfx)
        elif self._action == Action.SBSEARCH:
            # self._manager.ddf_method = self._ddf_method
            self.do_sb_search(print_options)
            self.print_search_report()
        elif self._action == Action.SBFIT:
            self.do_sb_fit(print_options)
        else:
            print("Error: unknown operation", self._action)

    def print_option(self, label: str, value: str) -> None:
        if self._HTMLFormat:
            print(f"<tr><td>{label}</td><td>{value}</td></tr>")
        else:
            print(f"{label},{value}")

    def print_options(self, r_type: int) -> None:
        if self._HTMLFormat:
            print("<br><table border=0 cellpadding=0 cellspacing=0>")
        self._manager.print_options(self._HTMLFormat, self._skip_nominal)
        self.print_option("Input data file", self._data_file)

        if self._fit_classifier_target != "":
            self.print_option(
                "Default ('negative') state for confusion matrices",
                self._fit_classifier_target,
            )
        if r_type == 1:
            self.print_option("Starting model", self.start_model)
            self.print_option("Search direction", self.search_dir)
            self.print_option("Ref model", self._ref_model)
            self.print_option("Models to consider", self._search_filter)
            self.print_option("Search width", self._search_width)
            self.print_option("Search levels", self._search_levels)
            self.print_option("Search sort by", self.sort_name)
            self.print_option("Search preference", self._search_sort_dir)
            self.print_option("Report sort by", self._report_sort_name)
            self.print_option("Report preference", self._sort_dir.value)

        if r_type == 0:
            self.print_option(
                "Generate hypergraph images",
                "Y" if self._generate_graph else "N",
            )
            self.print_option(
                "Generate Gephi files", "Y" if self._generate_gephi else "N"
            )

        if self._generate_graph:
            self.print_option(
                "Hypergraph layout style", str(self._layout_style)
            )
            self.print_option("Hypergraph image width", str(self._graph_width))
            self.print_option(
                "Hypergraph image height", str(self._graph_height)
            )
            self.print_option(
                "Hypergraph font size", str(self._graph_font_size)
            )
            self.print_option(
                "Hypergraph node size", str(self._graph_node_size)
            )

        if self._generate_gephi or self._generate_graph:
            self.print_option(
                f"Hide {'IV' if self.is_directed else 'IVI'} components in hypergraph",
                "Y" if self._hide_isolated else "N",
            )

        self.newl('</table>')
        sys.stdout.flush()

    def find_best_model(self) -> Dict:
        self._hide_intermediate_output = True

        # Initialize a manager and the starting model
        self._manager.ref_model = self._ref_model
        self._manager.search_direction = SearchDirection(self.search_dir)
        self._manager.search_type = self.search_type()

        # Set up the starting model
        start = (
            self._manager.top_ref_model
            if self.search_dir == SearchDirection.DOWN
            else self._manager.bottom_ref_model
        )
        start.level = 0  # Unused?
        self._manager.compute_l2_statistics(start)
        self._manager.compute_dependent_statistics(start)
        self._report.add_model(start)
        self._next_id = 1
        start.id_ = self._next_id
        start.progenitor = start

        # Perform the search to find the best model
        old_models = [start]
        for i in range(1, self._search_levels + 1):
            sys.stdout.write('.')
            new_models = self.process_level(
                i, old_models, i != self._search_levels
            )
            for model in new_models:
                self._manager.compute_l2_statistics(model)
                self._manager.compute_dependent_statistics(model)
                self._next_id += 1
                model.id_ = self._next_id
                self._report.add_model(model)
            old_models = new_models

        self._report.sort(self.sort_name, self._sort_dir)
        best = self._report.best_model_data()
        self._hide_intermediate_output = False
        return best

    # Not used?
    # def compute_unary_statistic(self, model, key, modname):
    #     return self._manager.computeUnaryStatistic(model, key, modname)

    # # Not used?
    # def compute_binary_statistic(self, compare_order, key):
    #     file_ref, model_ref, file_comp, model_comp = compare_order
    #     return self._manager.computeBinaryStatistic(
    #         file_ref, model_ref, file_comp, model_comp, key
    #     )
