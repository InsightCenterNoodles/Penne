from dataclasses import  dataclass
from typing import Optional

"""
Generic Classes
"""

class Message(object):
    """Generic Message Class for casting messages sent from server

    Attributes:
        dynamically added to each instance using the from dict method
    """

    @classmethod
    def from_dict(cls, raw_dict):
        """Function to generate generic message objects
        
        Recursively catches nested structures

        Parameters:
            raw_dict (dict) : dict to be cast as message object
        """

        processed_dict = {}
        for key, value in raw_dict.items():

            # Recursive case
            if isinstance(value, dict):
                processed_dict[key] = cls.from_dict(value)

            # Recursive case for list of objects
            elif value and isinstance(value, list) and isinstance(value[0], dict):
                obj_list = []
                for nested_dict in value:
                    obj_list.append(cls.from_dict(nested_dict))
                processed_dict[key] = obj_list

            else:
                processed_dict[key] = value

        obj = cls()
        obj.__dict__.update(processed_dict)
        return obj
    

    def as_dict(self):
        return self.__dict__


    def __getitem__(self, __name: str):
        return getattr(self, __name)


    def __repr__(self):
        return f"<<Message Obj: {self.__dict__}>>"


class HandleInfo(object):
    """Class to organize useful info for processing each type of message

    Attributes:
        specifier (str) : keyword for delegate and state maps
        action (str)    : action performed by message
    """

    def __init__(self, specifier, action):
        self.specifier = specifier
        self.action = action


"""
Client Messages
"""

@dataclass
class InvokeIDType(object):
    entity : Optional[list[int]] = None
    table : Optional[list[int]] = None
    plot : Optional[list[int]] = None

@dataclass
class IntroMessage(object):
    client_name: str

@dataclass
class InvokeMethodMessage(object):
    method : list[int]
    args : list[any]
    context : InvokeIDType = None
    invoke_id : str = None