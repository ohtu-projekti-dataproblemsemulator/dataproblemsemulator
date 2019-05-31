class Array:

    def __init__(self, shape):
        self.shape = shape
        self.filters = []

    def addfilter(self, custom_filter):
        self.filters.append(custom_filter)
        custom_filter.shape = self.shape

    def process(self, data, index_tuple=()):
        for f in self.filters:
            f.apply(data, (index_tuple))
