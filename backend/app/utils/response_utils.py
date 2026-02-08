def to_serializable(obj):
    if hasattr(obj, '__dict__'):
        return {key: to_serializable(value) for key, value in obj.__dict__.items()}
    if isinstance(obj, list):
        return [to_serializable(item) for item in obj]
    if isinstance(obj, dict):
        return {key: to_serializable(value) for key, value in obj.items()}
    return obj