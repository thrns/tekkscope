from typing import Any, Dict, List, Optional

from langchain_core.callbacks import BaseCallbackHandler


class LLMProgressHandler(BaseCallbackHandler):
    def __init__(self, forward_fn):
        self.forward = forward_fn
        self._buffer: List[str] = []
        self._prompt_preview: Optional[str] = None

    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any) -> None:
        try:
            self._prompt_preview = (prompts[0][:200] + "...") if prompts and len(prompts[0]) > 200 else (prompts[0] if prompts else None)
            self.forward(
                "LLM start",
                0,
                {
                    "phase": "llm_start",
                    "prompt_preview": self._prompt_preview,
                },
            )
        except Exception:
            pass

    def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        try:
            self._buffer.append(token)
            current_text = "".join(self._buffer)[-8000:]
            self.forward(
                "LLM token",
                0,
                {
                    "phase": "llm_token",
                    "token": token,
                    "current_text": current_text,
                    "prompt_preview": self._prompt_preview,
                },
            )
        except Exception:
            pass

    def on_llm_end(self, response, **kwargs: Any) -> None:
        try:
            final_text = getattr(response, "content", str(response))
            self.forward(
                "LLM end",
                0,
                {
                    "phase": "llm_end",
                    "final_text": final_text,
                    "prompt_preview": self._prompt_preview,
                },
            )
        except Exception:
            pass