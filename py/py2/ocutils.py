# coding=utf-8
# Copyright © 1990 The Portland State University OCCAM Project Team
# [This program is licensed under the GPL version 3 or later.]
# Please see the file LICENSE in the source
# distribution of this software for license terms.

# coding=utf8
import heapq
import ocGraph
import occam
import re
import sys
import time

totalgen = 0
totalkept = 0
max_memory_to_use = 8 * 2 ** 30


class OCUtils:
    # Separator styles for reporting
    TAB_SEP = 1
    COMMA_SEP = 2
    SPACE_SEP = 3
    HTML_FORMAT = 4

    def __init__(self, man="VB"):
        if man == "VB":
            self._manager = occam.VBMManager()
        else:
            self._manager = occam.SBMManager()
        self._action = ""
        self._alpha_threshold = 0.05
        self._bp_statistics = 0
        self._calc_expected_dv = 0
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
        self._HTMLFormat = 0
        self._incremental_alpha = 0
        self._layout_style = None
        self._next_id = 0
        self._no_ipf = 0
        self._percent_correct = 0
        self._ref_model = "default"
        self._report = self._manager.Report()
        self._report.setSeparator(
            OCUtils.SPACE_SEP
        )  # align columns using spaces
        self._report_file = ""
        self._report_sort_name = ""
        self._search_filter = "loopless"
        self._search_levels = 7
        self._search_sort_dir = "ascending"
        self._search_width = 3
        self._skip_ivi_tables = 1
        self._skip_nominal = 0
        self._skip_trained_model_table = 1
        self._sort_dir = "ascending"
        self._start_model = "default"
        self._total_gen = 0
        self._total_kept = 0
        self._use_inverse_notation = 0
        self._values_are_functions = 0
        self.graphs = {}
        self.search_dir = "default"
        self.sort_name = "ddf"
        # self._show_edge_weights = True
        # self._weight_fn = "Mutual Information"

    # -- Read command line args and process input file
    def init_from_command_line(self, argv):
        self._manager.initFromCommandLine(argv)
        self.occam2_settings()

    # -- Set up report variables
    def set_report_variables(self, report_attributes):
        # if the data uses function values, we want to skip the attributes that require a sample size
        option = self._manager.getOption("function-values")
        if option != "" or self._values_are_functions != 0:
            report_attributes = re.sub(r",\salpha", '', report_attributes)
            report_attributes = re.sub(r",\sincr_alpha", '', report_attributes)
            report_attributes = re.sub(r",\slr", '', report_attributes)
            report_attributes = re.sub(r",\saic", '', report_attributes)
            report_attributes = re.sub(r",\sbic", '', report_attributes)
            pass
        self._report.setAttributes(report_attributes)
        if re.search('bp_t', report_attributes):
            self._bp_statistics = 1
        if re.search('pct_correct', report_attributes):
            self._percent_correct = 1
        if re.search('incr_alpha', report_attributes):
            self._incremental_alpha = 1

    def set_report_separator(self, format_):
        occam.setHTMLMode(format_ == OCUtils.HTML_FORMAT)
        self._report.setSeparator(format_)
        self._HTMLFormat = format_ == OCUtils.HTML_FORMAT

    def set_fit_classifier_target(self, target):
        self._fit_classifier_target = target

    def set_skip_trained_model_table(self, b):
        self._skip_trained_model_table = b

    def set_skip_ivi_tables(self, b):
        self._skip_ivi_tables = b

    def set_skip_nominal(self, use_flag):
        flag = int(use_flag)
        if flag != 1:
            flag = 0
        self._skip_nominal = flag

    def set_use_inverse_notation(self, use_flag):
        flag = int(use_flag)
        if flag != 1:
            flag = 0
        self._use_inverse_notation = flag

    def set_values_are_functions(self, use_flag):
        flag = int(use_flag)
        if flag != 1:
            flag = 0
        self._values_are_functions = flag

    # -- Set control attributes
    def set_ddf_method(self, ddf_method):
        method = int(ddf_method)
        if method != 1:
            method = 0
        self._ddf_method = method

    def set_sort_dir(self, sort_dir):
        if sort_dir == "":
            sort_dir = "descending"
        if sort_dir != "ascending" and sort_dir != "descending":
            raise AttributeError("set_sort_dir")
        self._sort_dir = sort_dir

    def set_search_sort_dir(self, sort_dir):
        if sort_dir == "":
            sort_dir = "descending"
        if sort_dir != "ascending" and sort_dir != "descending":
            raise AttributeError("set_search_sort_dir")
        self._search_sort_dir = sort_dir

    def set_search_width(self, search_width):
        width = int(round(float(search_width)))
        if width <= 0:
            width = 1
        self._search_width = width

    def set_search_levels(self, search_levels):
        levels = int(round(float(search_levels)))
        if levels < 0:  # zero is OK here
            levels = 0
        self._search_levels = levels

    def set_report_sort_name(self, sort_name):
        self._report_sort_name = sort_name

    def set_search_filter(self, search_filter):
        self._search_filter = search_filter

    def set_alpha_threshold(self, alpha_threshold):
        self._alpha_threshold = float(alpha_threshold)

    def set_ref_model(self, ref_model):
        self._ref_model = ref_model

    def set_start_model(self, start_model):
        if not (start_model in ["top", "bottom", "default", ""]):
            self.check_model_name(start_model)
        self._start_model = start_model

    def get_start_model(self):
        return self._start_model

    def set_fit_model(self, fit_model):
        self._fit_models = [fit_model]

    def set_report_file(self, report_file):
        self._report_file = report_file

    def set_action(self, action):
        self._action = action

    def set_data_file(self, data_file):
        self._data_file = data_file

    def set_calc_expected_dv(self, calc_expected_dv):
        self._calc_expected_dv = calc_expected_dv

    def set_default_fit_model(self, model):
        self._default_fit_model = model

    def set_no_ipf(self, state):
        self._no_ipf = state

    def is_directed(self):
        return self._manager.isDirected()

    def has_test_data(self):
        return self._manager.hasTestData()

    # -- Search operations
    # compare function for sorting models. The python list sort function uses this
    # the name of the attribute to sort on is given above, as well as ascending or descending
    def _compare_models(self, m1, m2):
        result = 0
        a1 = m1.get(self.sort_name)
        a2 = m2.get(self.sort_name)
        if self._search_sort_dir == "ascending":
            if a1 > a2:
                result = 1
            if a1 < a2:
                result = -1
        else:
            if a1 > a2:
                result = -1
            if a1 < a2:
                result = 1
        return result

    # this function decides which statistic to computed, based
    # on how search is sorting the models. We want to avoid any
    # extra expensive computations
    def compute_sort_statistic(self, model):
        if self.sort_name in ("h", "information", "unexplained", "alg_t"):
            self._manager.computeInformationsStatistics(model)
        elif self.sort_name in ("df", "ddf"):
            self._manager.computeDFStatistics(model)
        elif self.sort_name in ("bp_t", "bp_information", "bp_alpha"):
            self._manager.computeBPStatistics(model)
        elif self.sort_name == "pct_correct_data":
            self._manager.computePercentCorrect(model)
        # anything else, just compute everything we might need
        else:
            self._manager.computeL2Statistics(model)
            self._manager.computeDependentStatistics(model)

    # this function generates the parents/children of the given model, and for
    # any which haven't been seen before puts them into the new_model list
    # this function also computes the LR statistics (H, LR, DF, etc.) as well
    # as the dependent statistics (dH, %dH, etc.)
    def process_model(self, level, new_models_heap, model):
        add_count = 0
        generated_models = self._manager.searchOneLevel(model)
        for new_model in generated_models:
            if new_model.get("processed") <= 0.0:
                new_model.processed = 1.0
                new_model.level = level
                new_model.setProgenitor(model)
                self.compute_sort_statistic(new_model)
                # need a fix here (or somewhere) to check for (and remove) models that have the same DF as the progenitor
                # decorate model with a key for sorting, & push onto heap
                key = new_model.get(self.sort_name)
                if self._search_sort_dir == "descending":
                    key = -key
                heapq.heappush(
                    new_models_heap, ([key, new_model.get("name")], new_model)
                )  # appending the model name makes sort alphabet-consistent
                add_count += 1
            else:
                if self._incremental_alpha:
                    # this model has been made already, but this progenitor might lead to a better Incr.Alpha
                    # so we ask the manager to check on that, and save the best progenitor
                    self._manager.compareProgenitors(new_model, model)
        return add_count

    # This function processes models from one level, and return models for the next level.
    def process_level(self, level, old_models, clear_cache_flag):
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
            if (
                len(best_models) < self._search_width
            ):  # or key[0] == last_key[0]:      # comparing keys allows us to select more than <width> models,
                if not any(
                    [n.isEquivalentTo(candidate) for n in best_models]
                ):  # in the case of ties
                    best_models.append(candidate)
            else:
                break
        trunc_count = len(best_models)
        self._total_gen = full_count + self._total_gen
        self._total_kept = trunc_count + self._total_kept
        mem_used = self._manager.getMemUsage()
        if not self._hide_intermediate_output:
            print '%d new models, %ld kept; %ld total models, %ld total kept; %ld kb memory used; ' % (
                full_count,
                trunc_count,
                self._total_gen + 1,
                self._total_kept + 1,
                mem_used / 1024,
            ),
        sys.stdout.flush()
        if clear_cache_flag:
            for item in new_models_heap:
                self._manager.deleteModelFromCache(item[1])
        return best_models

    # This function returns the name of the search strategy to use based on
    # the search_mode and loopless settings above
    def search_type(self):
        if self.search_dir == "up":
            if self._search_filter == "loopless":
                search_mode = "loopless-up"
            elif self._search_filter == "disjoint":
                search_mode = "disjoint-up"
            elif self._search_filter == "chain":
                search_mode = "chain-up"
            else:
                search_mode = "full-up"
        else:
            if self._search_filter == "loopless":
                search_mode = "loopless-down"
            elif self._search_filter == "disjoint":
                # This mode is not implemented
                search_mode = "disjoint-down"
            elif self._search_filter == "chain":
                # This mode is not implemented
                search_mode = "chain-down"
            else:
                search_mode = "full-down"
        return search_mode

    def sb_search_type(self):
        if self.search_dir == "up":
            if self._search_filter == "loopless":
                search_mode = "sb-loopless-up"
            elif self._search_filter == "disjoint":
                search_mode = "sb-disjoint-up"
            elif self._search_filter == "chain":
                search_mode = "sb-chain-up"
            else:
                search_mode = "sb-full-up"
        else:
            if self._search_filter == "loopless":
                search_mode = "sb-loopless-down"
            elif self._search_filter == "disjoint":
                # This mode is not implemented
                search_mode = "sb-disjoint-down"
            elif self._search_filter == "chain":
                # This mode is not implemented
                search_mode = "sb-chain-down"
            else:
                search_mode = "sb-full-down"
        return search_mode

    def do_search(self, print_options):
        if self._manager.isDirected():
            if self.search_dir == "down":
                if self._search_filter == "disjoint":
                    pass
                elif self._search_filter == "chain":
                    print 'ERROR: Directed Down Chain Search not yet implemented.'
                    raise sys.exit()
        else:
            if self.search_dir == "up":
                pass
            else:
                if self._search_filter == "disjoint":
                    pass
                elif self._search_filter == "chain":
                    print 'ERROR: Neutral Down Chain Search not yet implemented.'
                    raise sys.exit()

        if self._start_model == "":
            self._start_model = "default"
        if self.search_dir == "default":
            self.search_dir = "up"
        # set start model. For chain search, ignore any specific starting model
        # otherwise, if not set, set the start model based on search direction
        if (
            self._search_filter == "chain" or self._start_model == "default"
        ) and self.search_dir == "down":
            self._start_model = "top"
        elif (
            self._search_filter == "chain" or self._start_model == "default"
        ) and self.search_dir == "up":
            self._start_model = "bottom"
        if self._start_model == "top":
            start = self._manager.getTopRefModel()
        elif self._start_model == "bottom":
            start = self._manager.getBottomRefModel()
        else:
            start = self._manager.makeModel(self._start_model, 1)
        self.set_ref_model(self._ref_model)
        self._manager.setUseInverseNotation(self._use_inverse_notation)
        self._manager.setValuesAreFunctions(self._values_are_functions)
        self._manager.setAlphaThreshold(self._alpha_threshold)
        if self.search_dir == "down":
            self._manager.setSearchDirection(1)
        else:
            self._manager.setSearchDirection(0)
        if print_options:
            self.print_options(1)
        self._manager.printBasicStatistics()
        self._manager.computeL2Statistics(start)
        self._manager.computeDependentStatistics(start)
        if self._bp_statistics:
            self._manager.computeBPStatistics(start)
        if self._percent_correct and self._manager.isDirected():
            self._manager.computePercentCorrect(start)
        if self._incremental_alpha:
            self._manager.computeIncrementalAlpha(start)
        start.level = 0
        self._report.addModel(start)
        self._next_id = 1
        start.setID(self._next_id)
        start.setProgenitor(start)
        old_models = [start]
        try:
            self._manager.setSearchType(self.search_type())
        except Exception:
            print "ERROR: UNDEFINED SEARCH TYPE " + self.search_type()
            return
        # process each level, up to the number of levels indicated. Each of the best models
        # is added to the report generator for later output
        if self._HTMLFormat:
            print '<pre>'
        print "Searching levels:"
        start_time = time.time()
        last_time = start_time
        for i in xrange(1, self._search_levels + 1):
            if self._manager.getMemUsage() > max_memory_to_use:
                print "Memory limit exceeded: stopping search"
                break
            print i, ':',  # progress indicator
            new_models = self.process_level(
                i, old_models, i != self._search_levels
            )
            current_time = time.time()
            print '%.1f seconds, %.1f total' % (
                current_time - last_time,
                current_time - start_time,
            )
            sys.stdout.flush()
            last_time = current_time
            for model in new_models:
                # Make sure all statistics are calculated. This won't do anything if we did it already.
                if not self._no_ipf:
                    self._manager.computeL2Statistics(model)
                    self._manager.computeDependentStatistics(model)
                if self._bp_statistics:
                    self._manager.computeBPStatistics(model)
                if self._percent_correct:
                    self._manager.computePercentCorrect(model)
                if self._incremental_alpha:
                    self._manager.computeIncrementalAlpha(model)
                self._next_id += 1
                model.setID(self._next_id)
                # model.deleteFitTable()  #recover fit table memory
                self._report.addModel(model)
            old_models = new_models
            # if the list is empty, stop. Also, only do one step for chain search
            if self._search_filter == "chain" or len(old_models) == 0:
                break
        if self._HTMLFormat:
            print '</pre><br>'
        else:
            print ""

    def do_sb_search(self, print_options):
        if self._start_model == "":
            self._start_model = "default"
        if self.search_dir == "default":
            self.search_dir = "up"
        if (
            self._search_filter == "chain" or self._start_model == "default"
        ) and self.search_dir == "down":
            self._start_model = "top"
        elif (
            self._search_filter == "chain" or self._start_model == "default"
        ) and self.search_dir == "up":
            self._start_model = "bottom"
        if self._start_model == "top":
            start = self._manager.getTopRefModel()
        elif self._start_model == "bottom":
            start = self._manager.getBottomRefModel()
        else:
            start = self._manager.makeSbModel(self._start_model, 1)
        self.set_ref_model(self._ref_model)
        if self.search_dir == "down":
            self._manager.setSearchDirection(1)
        else:
            self._manager.setSearchDirection(0)
        if print_options:
            self.print_options(1)
        self._manager.printBasicStatistics()
        self._manager.computeL2Statistics(start)
        self._manager.computeDependentStatistics(start)
        if self._percent_correct and self._manager.isDirected():
            self._manager.computePercentCorrect(start)
        if self._incremental_alpha:
            self._manager.computeIncrementalAlpha(start)
        start.level = 0
        self._report.addModel(start)
        self._next_id = 1
        start.setID(self._next_id)
        start.setProgenitor(start)
        old_models = [start]
        try:
            self._manager.setSearchType(self.sb_search_type())
        except Exception:
            print "ERROR: UNDEFINED SEARCH TYPE " + self.sb_search_type()
            return
        if self._HTMLFormat:
            print '<pre>'
        print "Searching levels:"
        start_time = time.time()
        last_time = start_time
        for i in xrange(1, self._search_levels + 1):
            if self._manager.getMemUsage() > max_memory_to_use:
                print "Memory limit exceeded: stopping search"
                break
            print i, ':',  # progress indicator
            new_models = self.process_level(
                i, old_models, i != self._search_levels
            )
            current_time = time.time()
            print '%.1f seconds, %.1f total' % (
                current_time - last_time,
                current_time - start_time,
            )
            last_time = current_time
            for model in new_models:
                # Make sure all statistics are calculated. This won't do anything if we did it already.
                if not self._no_ipf:
                    self._manager.computeL2Statistics(model)
                    self._manager.computeDependentStatistics(model)
                if self._bp_statistics:
                    self._manager.computeBPStatistics(model)
                if self._percent_correct:
                    self._manager.computePercentCorrect(model)
                if self._incremental_alpha:
                    self._manager.computeIncrementalAlpha(model)
                self._next_id += 1
                model.setID(self._next_id)
                model.deleteFitTable()  # recover fit table memory
                self._report.addModel(model)
            old_models = new_models
            # if the list is empty, stop. Also, only do one step for chain search
            if self._search_filter == "chain" or len(old_models) == 0:
                break
        if self._HTMLFormat:
            print '</pre><br>'
        else:
            print ""

    def print_search_report(self):
        # sort the report as requested, and print it.
        if self._report_sort_name != "":
            sort_name = self._report_sort_name
        else:
            sort_name = self.sort_name
        self._report.sort(sort_name, self._sort_dir)
        if self._report_file != "":
            self._report.writeReport(self._report_file)
        else:
            self._report.printReport()

        # -- self._manager.dumpRelations()

    def print_search_graphs(self):

        if not (self._generate_graph or self._generate_gephi):
            return

        # in HTML mode, note that the graphs are being printed.
        if self._HTMLFormat:
            print '<hr>'

        # Get the varlist (used for all graphs)

        # Graphs for each kind of best model:
        # Generate the graph (but don't print anything yet).
        # BIC [1 or more]

        # AIC [1 or more]

        # Incr Alpha [0 or more]

        # For each of the graphs (and headers) above,
        # if HTML mode, print out a brief note and graph/gephi (if enabled)

    def newl(self):
        if self._HTMLFormat:
            print "<br>"

    @staticmethod
    def split_caps(s):
        return re.findall('[A-Z][^A-Z]*', s)

    def split_model(self, model_name):
        comps = model_name.split(":")
        model = map(
            lambda s: [s]
            if (s == "IV" if self.is_directed() else s == "IVI")
            else self.split_caps(s),
            comps,
        )
        return model

    def check_model_name(self, model_name):
        varlist = [v.getAbbrev() for v in self._manager.getVariableList()]
        model = self.split_model(model_name)
        is_directed = self.is_directed()
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

        if not have_ivs:
            if not varset.issubset(modset):
                if self._HTMLFormat:
                    print "<br>"
                print "\nERROR: Not all declared variables are present in the model, '" + model_name + "'."
                if self._HTMLFormat:
                    print "<br>"
                if saw_maybe_wrong_iv:
                    print "\n_did you mean '" + (
                        "IV" if is_directed else "IVI"
                    ) + "' instead of '" + (
                        "IVI" if is_directed else "IV"
                    ) + "'?"
                else:
                    print "\n Did you forget the " + (
                        "IV" if is_directed else "IVI"
                    ) + " component?"
                if self._HTMLFormat:
                    print "<br>"
                print "\n Not in model: "
                print ", ".join(
                    ["'" + i + "'" for i in varset.difference(modset)]
                )
                sys.exit(1)

        # all variables in model are in varlist
        if not modset.issubset(varset):
            if self._HTMLFormat:
                print "<br>"
            print "\nERROR: Not all variables in the model '" + model_name + "' are declared in the variable list."
            if self._HTMLFormat:
                print "<br>"
            diffset = modset.difference(varset)
            if saw_maybe_wrong_iv or diffset == {"I", "V"}:
                print "\n_did you mean '" + (
                    "IV" if is_directed else "IVI"
                ) + "' instead of '" + ("IVI" if is_directed else "IV") + "'?"
            else:
                print "\n Not declared: "
                print ", ".join(["'" + i + "'" for i in diffset])

            sys.exit(1)

        # dv must be in all components (except IV) if directed
        if is_directed:
            dv = self._manager.getDvName()
            for rel in model:
                if not (rel == ["IVI"] or rel == ["IV"]) and dv not in rel:
                    if self._HTMLFormat:
                        print "<br>"
                    print "\nERROR: In the model '" + model_name + "', model component '" + "".join(
                        rel
                    ) + "' is missing the DV, '" + dv + "'."
                    sys.exit(1)

    def print_graph(self, model_name, only):
        if only and not self._generate_gephi:
            self._generate_graph = True
        if (self._generate_graph or self._generate_gephi) and (
            self._hide_isolated and model_name in ("IV", "IVI")
        ):
            msg = "Note: no "
            if self._generate_graph:
                msg = msg + "hypergraph image "
            if self._generate_graph and self._generate_gephi:
                msg = msg + "or "
            if self._generate_gephi:
                msg = msg + "Gephi input "

            msg = msg + "was generated, since the model contains only "
            msg = msg + model_name
            msg = (
                "%s components, which were requested to be hidden in the graph."
                % msg
            )

            if self._HTMLFormat:
                print "<br>"
            print msg
            if self._HTMLFormat:
                print "<br>"

        else:
            self.maybe_print_graph_svg(model_name, True)
            self.maybe_print_graph_gephi(model_name, True)
        print
        print

    def do_fit(self, print_options, only_gfx):
        # self._manager.setValuesAreFunctions(self._values_are_functions)

        if print_options and not only_gfx:
            self.print_options(0)

        if not only_gfx:
            self._manager.printBasicStatistics()

        for model_name in self._fit_models:
            self.check_model_name(model_name)
            self.set_ref_model(self._ref_model)
            model = self._manager.makeModel(model_name, 1)

            if only_gfx:
                self.print_graph(model_name, only_gfx)
                continue

            self.do_all_computations(model)

            if self._default_fit_model != "":
                try:
                    default_model = self._manager.makeModel(
                        self._default_fit_model, 1
                    )
                except Exception:
                    print "\nERROR: Unable to create model " + self._default_fit_model
                    sys.exit(0)
                self._report.setDefaultFitModel(default_model)
            self._report.printConditional_DV(
                model, self._calc_expected_dv, self._fit_classifier_target
            )

            self.print_graph(model_name, only_gfx)

    def maybe_print_graph_svg(self, model, header):

        if self._generate_graph:
            self.generate_graph(model)
            if self._HTMLFormat:
                if header:
                    print "Hypergraph model visualization for the Model " + model + " (using the " + self._layout_style + " layout algorithm)<br>"
                ocGraph.print_svg(
                    self.graphs[model],
                    self._layout_style,
                    self._graph_width,
                    self._graph_height,
                    self._graph_font_size,
                    self._graph_node_size,
                )
                print "<hr>"

    def maybe_print_graph_gephi(self, model, header):

        if self._generate_gephi:
            self.generate_graph(model)

            if self._HTMLFormat:
                if header:
                    print "Hypergraph model Gephi input for the Model " + model + "<br>"
                print ocGraph.print_gephi(self.graphs[model])
                print "<hr>"

    def generate_graph(self, model):
        varlist = self._report.variableList()
        hide_iv = self._hide_isolated
        hide_dv = self._graph_hideDV
        full_var_names = self._full_var_names
        dv_name = ""
        all_higher_order = self._layout_style == "bipartite"
        if self.is_directed():
            dv_name = self._report.dvName()

        if model in self.graphs:
            pass
        else:
            self.graphs[model] = ocGraph.generate(
                model,
                varlist,
                hide_iv,
                hide_dv,
                dv_name,
                full_var_names,
                all_higher_order,
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
    ):
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

    def do_all_computations(self, model):
        self._manager.computeL2Statistics(model)
        self._manager.computeDFStatistics(model)
        self._manager.computeDependentStatistics(model)
        self._report.addModel(model)
        self._manager.printFitReport(model)
        self._manager.makeFitTable(model)
        self._report.printResiduals(
            model, self._skip_trained_model_table, self._skip_ivi_tables
        )

    def do_sb_fit(self, print_options):
        # self._manager.setValuesAreFunctions(self._values_are_functions)
        if print_options:
            self.print_options(0)
        self._manager.printBasicStatistics()
        for model_name in self._fit_models:
            self.set_ref_model(self._ref_model)
            model = self._manager.makeSbModel(model_name, 1)
            self.do_all_computations(model)
            if self._default_fit_model != "":
                try:
                    default_model = self._manager.makeSbModel(
                        self._default_fit_model, 1
                    )
                except Exception:
                    print "\nERROR: Unable to create model " + self._default_fit_model
                    sys.exit(0)
                self._report.setDefaultFitModel(default_model)
            self._report.printConditional_DV(
                model, self._calc_expected_dv, self._fit_classifier_target
            )

            print
            print

    def occam2_settings(self):
        option = self._manager.getOption("action")
        if option != "":
            self._action = option
        option = self._manager.getOption("search-levels")
        if option != "":
            self._search_levels = int(float(option))
        option = self._manager.getOption("optimize-search-width")
        if option != "":
            self._search_width = int(float(option))
        option = self._manager.getOption("reference-model")
        if option != "":
            self._ref_model = option
        option = self._manager.getOption("search-direction")
        if option != "":
            self.search_dir = option
        option = self._manager.getOptionList("short-model")
        # for search, only one specified model allowed
        if len(option) > 0:
            self._start_model = option[0]
            self._fit_models = option

    def do_action(self, print_options, only_gfx=False):
        # set reporting variables based on ref model
        if self._manager.isDirected() and self._ref_model == "default":
            if self.search_dir == "down":
                self._ref_model = "top"
            else:
                self._ref_model = "bottom"
        if not self._manager.isDirected() and self._ref_model == "default":
            if self.search_dir == "down":
                self._ref_model = "top"
            else:
                self._ref_model = "bottom"
        option = self._action
        if option == "search":
            self._manager.setDDFMethod(self._ddf_method)
            self.do_search(print_options)
            self.print_search_report()
        elif option == "fit":
            self._manager.setDDFMethod(self._ddf_method)
            self.do_fit(print_options, only_gfx)
        elif option == "SBsearch":
            # self._manager.setDDFMethod(self._DDFMethod)
            self.do_sb_search(print_options)
            self.print_search_report()
        elif option == "SBfit":
            self.do_sb_fit(print_options)
        else:
            print "Error: unknown operation", self._action

    def print_option(self, label, value):
        if self._HTMLFormat:
            print "<tr><td>" + label + "</td><td>" + str(value) + "</td></tr>"
        else:
            print label + "," + str(value)

    def print_options(self, r_type):
        if self._HTMLFormat:
            print "<br><table border=0 cellpadding=0 cellspacing=0>"
        self._manager.printOptions(self._HTMLFormat, self._skip_nominal)
        self.print_option("Input data file", self._data_file)

        if self._fit_classifier_target != "":
            self.print_option(
                "Default ('negative') state for confusion matrices",
                self._fit_classifier_target,
            )
        if r_type == 1:
            self.print_option("Starting model", self._start_model)
            self.print_option("Search direction", self.search_dir)
            self.print_option("Ref model", self._ref_model)
            self.print_option("Models to consider", self._search_filter)
            self.print_option("Search width", self._search_width)
            self.print_option("Search levels", self._search_levels)
            self.print_option("Search sort by", self.sort_name)
            self.print_option("Search preference", self._search_sort_dir)
            self.print_option("Report sort by", self._report_sort_name)
            self.print_option("Report preference", self._sort_dir)

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
                "Hide "
                + ("IV" if self.is_directed() else "IVI")
                + " components in hypergraph",
                "Y" if self._hide_isolated else "N",
            )

        if self._HTMLFormat:
            print "</table>"
        sys.stdout.flush()

    def find_best_model(self):
        self._hide_intermediate_output = True

        # Initialize a manager and the starting model
        self.set_ref_model(self._ref_model)
        self._manager.setSearchDirection(
            1 if (self.search_dir == "down") else 0
        )
        self._manager.setSearchType(self.search_type())

        # Set up the starting model
        start = (
            self._manager.getTopRefModel()
            if (self.search_dir == "down")
            else self._manager.getBottomRefModel()
        )
        start.level = 0
        self._manager.computeL2Statistics(start)
        self._manager.computeDependentStatistics(start)
        self._report.addModel(start)
        self._next_id = 1
        start.setID(self._next_id)
        start.setProgenitor(start)

        # Perform the search to find the best model
        old_models = [start]
        for i in xrange(1, self._search_levels + 1):
            sys.stdout.write('.')
            new_models = self.process_level(
                i, old_models, i != self._search_levels
            )
            for model in new_models:
                self._manager.computeL2Statistics(model)
                self._manager.computeDependentStatistics(model)
                self._next_id += 1
                model.setID(self._next_id)
                self._report.addModel(model)
            old_models = new_models

        self._report.sort(self.sort_name, self._sort_dir)
        best = self._report.bestModelData()
        self._hide_intermediate_output = False
        return best

    def compute_unary_statistic(self, model, key, modname):
        return self._manager.computeUnaryStatistic(model, key, modname)

    def compute_binary_statistic(self, compare_order, key):
        file_ref, model_ref, file_comp, model_comp = compare_order
        return self._manager.computeBinaryStatistic(
            file_ref, model_ref, file_comp, model_comp, key
        )
