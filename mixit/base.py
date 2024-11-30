from typing import ClassVar, List, Any
import logging

logger = logging.getLogger(__name__)

class Mixin:
	"""Base class for all mixins."""
	
	_exports: ClassVar[List[str]] = []
	_mixer_attr: ClassVar[str] = 'mixer'  # Default mixer attribute name
	
	def __init__(self):
		# Initialize mixer storage with None
		setattr(self, f"_{self._mixer_attr}", None)
		
	def __init_subclass__(cls, *, mixer_attr: str = None, **kwargs):
		super().__init_subclass__(**kwargs)
		cls._exports = []
		if mixer_attr is not None:
			cls._mixer_attr = mixer_attr
		
		# Collect exported methods
		for name, value in cls.__dict__.items():
			if getattr(value, '_is_exported', False):
				cls._exports.append(name)
				logger.debug(f"Found exported method '{name}' in mixin {cls.__name__}")
	
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
