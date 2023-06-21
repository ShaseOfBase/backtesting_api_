

def get_suggested_value(trial, suggestion_key: str, value: list):
    value_type = 'int'
    for sub_value in value:
        if isinstance(sub_value, float):
            value_type = 'float'
            break

    if value_type == 'int':
        if len(value) == 2:
            return trial.suggest_int(suggestion_key, *value)
        elif len(value) == 3:
            return trial.suggest_int(suggestion_key, *value, step=value[2])
        else:
            raise ValueError(f'Invalid length of value: {value}')

    elif value_type == 'float':
        if len(value) == 2:
            return trial.suggest_float(suggestion_key, *value)
        elif len(value) == 3:
            return trial.suggest_float(suggestion_key, *value, step=value[2])
        else:
            raise ValueError(f'Invalid length of value: {value}')

    else:
        raise ValueError(f'Invalid value_type: {value_type}')