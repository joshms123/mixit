from typing import ClassVar, List, Any
import logging

logger = logging.getLogger(__name__)

class Mixin:
	"""Base class for all mixins."""
	
	_exports: ClassVar[List[str]] = []
	
	def __init__(self):
		self._mixer = None  # Will be set by Mixer when added
		
	def __init_subclass__(cls, **kwargs):
		super().__init_subclass__(**kwargs)
		cls._exports = []
		
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
	
	@property
	def mixer(self):
		"""Get the mixer instance this mixin is attached to."""
		if self._mixer is None:
			raise RuntimeError(f"Mixin {self.__class__.__name__} is not attached to a mixer")
		return self._mixer
