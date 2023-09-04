{% macro APP() -%}
    {{ params.app_abbreviation_upper }}
{%- endmacro %}
import pandas                                                       as _pd

from conway.application.application                                 import Application as {{ APP() }}
from conway.database.data_accessor                                  import DataAccessor

from conway.util.dataframe_utils                                    import DataFrameUtils
from conway.util.profiler                                           import Profiler

from {{params.app_module}}.util.static_globals                      import DataHubSchema

class CalculatorService():

    '''
    Sample service to illustrate how to write services that perform calculations
    '''
    def __init__(self, config):

        self.config                                     = config

    '''
    Computes a price for a bid involving a number of products and services, and generates and returns a DataFrame that contains 
    the details of what the products and services it covers, as well as the itemized pricing for each item.

    :param dict bid: A dictionary of properties for the bid to be priced, including a subdictionary defining the scope of the 
        bid. For that sub-dictinoary, keys represent the various products and services in the scope of the quote,
        and the dictionary values represent the number of units for each product or service.

    :returns: A DataFrame with 3 columns, for the product, the amount, and the total cost.
    :rtype: ``pandas.DataFrame``
    '''
    def get_quote(self, bid):
        with Profiler("Obtaining a quote"):
            DHS                                             = DataHubSchema()
            customer                                        = bid["customer_name"]
            region                                          = bid["region"]
            scope_dict                                      = bid["scope"] # This determines which products/amounts are included in the order

 

            {{ APP() }}.app().log(f"Loading market data for region {region}")
            # Market data for regions is stored in an Excel spreadsheet, with a dedicated tab per region. The Excel tab
            # determines the ``subpath`` parameter in the DataAccessor context manager
            #
            market_data_path                                = f"{self.config.marketdata_hub}/{DHS.MARKET_DATA_REGIONS}"
            with DataAccessor(market_data_path, subpath=region) as ax:
                regional_prices_df                          = ax.retrieve()

            {{ APP() }}.app().log(f"Pricing quote for {customer}")
            scope_df                                        = _pd.DataFrame({DHS.PRODUCT_COL: list(scope_dict.keys()),
                                                                            DHS.AMOUNT_COL: list(scope_dict.values())})                                

            # regional_prices_df is expected to contain two columns: one to identify the product, one for unit costs.
            # We want to join those unit costs for the products/amounts that are in scope_df
            #
            joinable_df                                     = regional_prices_df.set_index(DHS.PRODUCT_COL)

            quote_df                                        = scope_df.join(joinable_df, on=DHS.PRODUCT_COL)

            quote_df["Total"]                               = quote_df[DHS.AMOUNT_COL] * quote_df[DHS.UNIT_COST_COL]

            return quote_df