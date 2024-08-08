from eocanvas.exceptions import SnapOperatorNotFound

from .snap import Snap


class OperatorParams:
    def __init__(self, operator):
        self._snap_operators = Snap().operators
        if operator not in self._snap_operators:
            raise SnapOperatorNotFound(f"Operator {operator} not recognized.")

        self.operator = operator
        params = self._snap_operators[operator]["params"].keys()
        self.params = {
            param: self._snap_operators[operator]["params"][param].get("default_values")
            for param in params
        }
