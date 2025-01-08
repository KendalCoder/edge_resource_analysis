def convert_to_bytes(value):
    """
    Convert a value to bytes.
    """
    if value[-2:] == 'Mi':
        return int(value[:-2]) * 1024 * 1024
    elif value[-2:] == 'Gi':
        return int(value[:-2]) * 1024 * 1024 * 1024
    else:
        return int(value)
    
def convert_to_millicores(value):
    """
    Convert a value to millicores.
    """
    if value[-1] == 'm':
        return int(value[:-1])
    elif value[-1] == 'n':
        return int(value[:-1]) / 1000000
    else:
        return int(value) * 1000