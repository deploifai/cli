class DeploifaiAPIError(Exception):
    """
    Exception when API calls result in an error.
    """

    def __init__(self, message):
        super(DeploifaiAPIError, self).__init__(message)
