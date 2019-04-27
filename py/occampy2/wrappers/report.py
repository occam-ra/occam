class Report:
    """
    Wrapper class for Report
    """

    def __init__(self, ref):
        """
        :param: ref: the reference to the Report object returned from the CPP engine
        """
        self._ref = ref  # type Report_cpp
