
class CalculatorServiceConfig():

    '''
    Helper class used to hold all the properties that are part of the configuration for the CalculatorService class.

    :param str marketdata_hub: represents a path, URL or equivalent, servicng as the root area for the datasources
        containing market data that the CalculatorService must rely on.

    :param str storage_hub: represents a path, URL or equivalent to identify the root area under which the CalculatorService
        should store its results.

    :param dict pricing_policy: contains settings for the mathematical algorithms used by the CalculatorService
    '''
    def __init__(self, marketdata_hub, storage_hub, pricing_policy):
        self.marketdata_hub                         = marketdata_hub
        self.storage_hub                            = storage_hub
        self.pricing_policy                         = pricing_policy