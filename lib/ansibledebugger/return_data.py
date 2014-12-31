
from ansible.runner.return_data import ReturnData


class ReturnDataWithoutSlots(ReturnData):
    """Almost same as  ReturnData class, except that it is allowed to
    dynamically add an attribute.
    """
    def __init__(self, return_data):
        for attr in ReturnData.__slots__:
            value = getattr(return_data, attr)
            setattr(self, attr, value)

        self.original_return_data = return_data
