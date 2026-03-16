from input_engine.handlers.text import TextHandler
from input_engine.registry import register

# Auto-register handlers on import
_text_handler = TextHandler()
register("text", _text_handler)
register("markdown", _text_handler)
