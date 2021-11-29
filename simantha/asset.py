class Asset:
    """Parent class for assets in the system. All objects should extend this class."""
    
    def __init__(self, name):
        self.name = name

        self.upstream = []
        self.downstream = []

    def initialize(self):
        pass

    def get_candidate_givers(self, blocked=False):
        """
        Returns a list of assets that can give a part to this asset from among the
        upstream assets. 

        If 'blocked=True' then only return assets that are currently blocked. 
        """
        candidates = []
        for candidate in self.upstream:
            if blocked:
                if candidate.blocked:
                    candidates.append(candidate)
