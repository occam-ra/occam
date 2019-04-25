class Variable:
    def __init__(self, ref) -> None:
        self._ref = ref

    def get_abbrev(self) -> str:
        return self._ref.getAbbrev()
