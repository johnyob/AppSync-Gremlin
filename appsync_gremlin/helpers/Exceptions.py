from typing import Any, Dict


class AppSyncException(Exception):

    def __init__(self, error_type: str, error_message: str, error_data: Dict[str, Any]):

        self._error_type = error_type
        self._error_message = error_message
        self._error_data = error_data

    @property
    def error_message(self) -> str:
        return self._error_message

    @property
    def error_type(self) -> str:
        return self._error_type

    @property
    def error_data(self) -> Dict[str, Any]:
        return self._error_data

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error_type": self.error_type,
            "error_message": self.error_message,
            "data": self.error_data
        }

