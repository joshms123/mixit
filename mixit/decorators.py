from functools import wraps
from typing import Callable, TypeVar, Any, Optional

F = TypeVar('F', bound=Callable[..., Any])

def export(method: Optional[F] = None) -> F:
        """Decorator to mark methods that should be exported to the Mixer namespace."""
        def decorator(func: F) -> F:
                @wraps(func)
                def wrapper(self, *args, **kwargs):
                        return func(self, *args, **kwargs)
                
                wrapper._is_exported = True
                return wrapper
        
        if method is None:
                return decorator
        return decorator(method)
