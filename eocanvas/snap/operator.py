from types import SimpleNamespace

from eocanvas.exceptions import SnapOperatorNotFound

from .operatorparams import OperatorParams
from .snap import Snap


class Operator(SimpleNamespace):
    def __init__(self, operator, **kwargs):
        self._snap_operators = Snap().operators
        if operator not in self._snap_operators:
            raise SnapOperatorNotFound(f"Operator {operator} not recognized.")
        self.operator = operator
        self._params = {**OperatorParams(self.operator).params, **kwargs}
        super().__init__(**self._params)

    def __str__(self):
        return "{}:\n\t{}".format(
            self.operator,
            "\n\t".join(["{}='{}'".format(key, value) for key, value in self.to_dict().items()]),
        )

    def __repr__(self):
        return "Operator('{}', {})".format(
            self.operator,
            ", ".join(["{}='{}'".format(key, value) for key, value in self.to_dict().items()]),
        )

    def to_dict(self):
        return dict([(name, getattr(self, name)) for name in list(self._params.keys())])

    def describe(self):
        """This function prints the human readable information about a SNAP operator

        Args:
            operator: SNAP operator

        Returns
            The human readable information about the provided SNAP operator.

        Raises:
            None.
        """
        operator = self._snap_operators[self.operator]
        print(f"Operator name: {operator['alias']}\n")
        print(f"Description: {operator['description']}")
        print(f"Authors: {operator['authors']}\n")
        print(f"{operator['name']}")
        print(f"Version: {operator['version']}\n")
        print("Parameters:\n")

        for name, param in operator["params"].items():
            print(
                f"\t{name}: {param['description']}\n\t\tDefault Value: {param['default_values']}\n"
            )
            print(f"\t\tPossible values: {param['values_set']}\n")

    @staticmethod
    def _get_formats(method):
        """This function provides a human readable list of SNAP Read or Write operator formats.

        Args:
            None.

        Returns
            Human readable list of SNAP Write operator formats.

        Raises:
            None.
        """

        if method == "Read":
            return Snap().read_formats
        elif method == "Write":
            return Snap().write_formats
        else:
            raise ValueError
