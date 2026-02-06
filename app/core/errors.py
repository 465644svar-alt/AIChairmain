class CouncilError(Exception):
    """Base error for arbitration pipeline."""


class ProviderError(CouncilError):
    pass


class Stage2ParseError(CouncilError):
    pass
