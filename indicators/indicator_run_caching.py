cached_results = {}


def get_guid(data_instance, indicator: str, run_kwargs: dict = None):
    '''Returns a guid from data_instance, indicator, timeframe, run_kwargs'''
    return f'{id(data_instance)}_{indicator}_{run_kwargs}'


def get_cached_indicator_run_result(data_instance, indicator: str, run_kwargs: dict = None):
    '''Returns the cached results of the run_values for the indicator'''

    guid = get_guid(data_instance, indicator, run_kwargs)
    if guid not in cached_results:
        return None

    return cached_results[guid]


def cache_indicator_run_result(run_result, data_instance, indicator: str, run_kwargs: dict = None):
    '''Caches the results of the run_values for the indicator'''

    guid = get_guid(data_instance, indicator, run_kwargs)
    if guid in cached_results:
        raise ValueError(f'{guid} already exists in cached_results')

    cached_results[guid] = run_result


def clear_indicator_run_cache():
    '''Clears the cached_results'''
    cached_results.clear()