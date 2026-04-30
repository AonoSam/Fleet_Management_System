import uuid


def generate_reference():
    return str(uuid.uuid4()).replace('-', '')[:10]