"""Custom exceptions for OMR system."""


class ValidationError(Exception):
    """Raised when user input validation fails. Safe to display to users."""

    def get_user_message(self) -> str:
        """Get the user-facing error message."""
        return str(self.args[0]) if self.args else "Erro de validação"
