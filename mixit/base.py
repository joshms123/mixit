from typing import ClassVar, List, Any
import logging

logger = logging.getLogger(__name__)

class Mixin:
        """Base class for all mixins."""
        
        _exports: ClassVar[List[str]] = []
        _mixer_attr: ClassVar[str] = 'mixer'  # Default mixer attribute name
        export_prefix: ClassVar[str] = None  # Default export prefix
        
        def __init__(self):
                # Initialize mixer storage with None
                setattr(self, f"_{self._mixer_attr}", None)
                
        def __init_subclass__(cls, *, mixer_attr: str = None, export_prefix: str = None, **kwargs):
                super().__init_subclass__(**kwargs)
                cls._exports = []
                
                if mixer_attr is not None:
                        cls._mixer_attr = mixer_attr
                if export_prefix is not None:
                        cls.export_prefix = export_prefix
                elif not hasattr(cls, 'export_prefix'):
                        # Inherit export_prefix from first parent that has it
                        for base in cls.__bases__:
                                if hasattr(base, 'export_prefix'):
                                        cls.export_prefix = base.export_prefix
                                        break
                
                # Collect exported methods from this class and parent classes
                for name, value in cls.__dict__.items():
                        # Check for explicitly exported methods
                        if getattr(value, '_is_exported', False):
                                cls._exports.append(name)
                                logger.debug(f"Found exported method '{name}' in mixin {cls.__name__}")
                        # Check for prefix-based auto-export
                        elif (cls.export_prefix and 
                              callable(value) and 
                              name.startswith(cls.export_prefix)):
                                cls._exports.append(name)
                                logger.debug(f"Auto-exported method '{name}' in mixin {cls.__name__}")
                
                # Collect inherited methods that match the prefix
                if cls.export_prefix:
                        # Get all parent classes except Mixin
                        bases = [base for base in cls.__mro__[1:] if base is not Mixin and base is not object]
                        
                        # Collect methods from all parent classes
                        for base in bases:
                                for name, value in base.__dict__.items():
                                        if (name not in cls._exports and  # Don't duplicate if overridden
                                            callable(value) and
                                            name.startswith(cls.export_prefix)):
                                                cls._exports.append(name)
                                                logger.debug(f"Auto-exported inherited method '{name}' from {base.__name__} in {cls.__name__}")
        
        def mix_init(self, **kwargs) -> None:
                """Optional initialization method called after mixin is added."""
                pass
        
        def cleanup(self) -> None:
                """Clean up resources. Called when removing the mixin."""
                logger.info(f"Cleaning up mixin {self.__class__.__name__}")
        
        def set_mixer(self, mixer: Any) -> None:
                """Set the mixer instance for this mixin."""
                setattr(self, f"_{self._mixer_attr}", mixer)
                
        def __getattr__(self, name):
                """Support custom mixer attribute name."""
                if name == self._mixer_attr:
                        value = getattr(self, f"_{name}")
                        if value is None:
                                raise RuntimeError(f"Mixin {self.__class__.__name__} is not attached to a mixer")
                        return value
                raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
