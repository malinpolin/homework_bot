class MissingEnvVarError(Exception):
    """Исключение возникает при отсутствии обязательной 
    переменной окружения.
    """
    def __init__(self, var_name, message):
        self.message = message
        self.var_name = var_name

    def __str__(self):
        return f'{self.message}: {self.var_name}'


class StatusCodeError(Exception):
    """Исключение возникает в случае, если статус код != 200."""
    ...


class EmptyResponseError(Exception):
    """Исключение возникает, если пришел пустой ответ от сервера."""
    ...


class InvalidTypeResponseError(Exception):
    """Исключение возникает, если тип ответа от эндпоинта не dict."""
    ...


class HomeworksTypeError(Exception):
    """Исключение возникает, если список домашних работ не в формате list."""
    ...


class HomeworksKeyError(Exception):
    """Исключение возникает, если в ответе остутствует ключ 'homeworks'."""
    ...


class UnknownHomeworkStatusError(Exception):
    """Исключение возникает, если статус домашней работы неизвестен."""
    ...


class StatusKeyError(Exception):
    """Исключение возникает, если в домашней работе
    остутствует ключ 'status'."""
    ...

class EmptyHomeworkNameError(Exception):
    """Исключение возникает, если в домашней работе
    остутствует ключ 'homework_name'."""
    ...

