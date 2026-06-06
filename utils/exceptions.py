from utils.models import Word

class LanmoSyntaxError(Exception):
    def __init__(self, token: Word | None, message: str):
        super().__init__(message)
        print(token.get_line())
        self.token = token