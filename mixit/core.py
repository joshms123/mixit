from typing import Type, Dict, List, Any
import logging

from .base import Mixin
from .exceptions import (
	MixinNotFoundError,
	DuplicateMixinError,
	InvalidMixinError
)

logger = logging.getLogger(__name__)

class Mixer:
	"""
	A central mixer that manages mixins and their exported methods.
	"""
	def __init__(self):
		self._mixins: Dict[str, Mixin] = {}
		self._method_conflicts: Dict[str, List[str]] = {}
		logger.info("Initialized new Mixer instance")
	
	def add_mixin_instance(self, name: str, instance: Mixin) -> Mixin:
		"""
		Add an existing mixin instance to the mixer.
		
		Args:
			name: The attribute name to access the mixin instance
			instance: The mixin instance to add
			
		Returns:
			The added mixin instance
			
		Raises:
			InvalidMixinError: If instance is not a Mixin instance
			DuplicateMixinError: If name is already in use
		"""
		# Validate mixin instance
		if not isinstance(instance, Mixin):
			raise InvalidMixinError(f"{instance.__class__.__name__} must be an instance of Mixin")
		
		# Check for name conflicts
		if name in self._mixins:
			raise DuplicateMixinError(f"Mixin name '{name}' is already in use")
		
		logger.debug(f"Adding mixin instance '{name}' ({instance.__class__.__name__})")
		
		# Set mixer using the set_mixer method
		instance.set_mixer(self)
		
		# Store the instance
		self._mixins[name] = instance
		setattr(self, name, instance)
		
		# Export methods
		for method_name in instance.__class__._exports:
			if hasattr(self, method_name):
				# Track conflicts but don't export
				self._method_conflicts.setdefault(method_name, []).append(name)
				logger.warning(f"Method '{method_name}' from mixin '{name}' conflicts with existing method and was not exported")
			else:
				method = getattr(instance, method_name)
				setattr(self, method_name, method)
				logger.debug(f"Exported method '{method_name}' from mixin '{name}'")
		
		return instance
	
	def add_mixin(self, name: str, mixin_class: Type[Mixin], **kwargs) -> Mixin:
		"""
		Create and add a mixin instance to the mixer.
		
		Args:
			name: The attribute name to access the mixin instance
			mixin_class: The mixin class to instantiate and mix in
			**kwargs: Additional arguments passed to mix_init
			
		Returns:
			The created and added mixin instance
			
		Raises:
			InvalidMixinError: If mixin_class is not a Mixin subclass
			DuplicateMixinError: If name is already in use
		"""
		# Validate mixin class
		if not isinstance(mixin_class, type) or not issubclass(mixin_class, Mixin):
			raise InvalidMixinError(f"{mixin_class.__name__} must be a subclass of Mixin")
		
		logger.debug(f"Creating mixin instance of {mixin_class.__name__}")
		
		# Create instance
		instance = mixin_class()
		
		# Add the instance and initialize it
		self.add_mixin_instance(name, instance)
		instance.mix_init(**kwargs)
		
		return instance
	
	def remove_mixin(self, name: str) -> None:
		"""Remove a mixin from the mixer."""
		try:
			mixin = self._mixins[name]
		except KeyError:
			raise MixinNotFoundError(f"Mixin '{name}' not found")
		
		logger.info(f"Removing mixin '{name}'")
		
		# Clean up mixin
		mixin.cleanup()
		
		# Remove exported methods
		for method_name in mixin.__class__._exports:
			if hasattr(self, method_name):
				delattr(self, method_name)
		
		# Remove mixin
		del self._mixins[name]
		delattr(self, name)
		
		# Clean up conflict tracking
		for conflicts in self._method_conflicts.values():
			if name in conflicts:
				conflicts.remove(name)
	
	def get_mixin(self, name: str) -> Mixin:
		"""Get a mixin instance by name."""
		try:
			return self._mixins[name]
		except KeyError:
			raise MixinNotFoundError(f"Mixin '{name}' not found")
	
	def get_mixins(self) -> Dict[str, Mixin]:
		"""Get all mixed-in instances."""
		return self._mixins.copy()
	
	def get_conflicts(self) -> Dict[str, List[str]]:
		"""Get information about method export conflicts."""
		return self._method_conflicts.copy()
	
	def call_all_mixins(self, func_name: str, *args, **kwargs) -> Dict[str, Any]:
		"""
		Call a function on all mixins that have it with the given arguments.
		
		Args:
			func_name: Name of the function to call on each mixin
			*args: Positional arguments to pass to the function
			**kwargs: Keyword arguments to pass to the function
			
		Returns:
			Dict mapping mixin names to their function results
		
		Raises:
			AttributeError: If no mixin has the specified function or if it exists but is not callable
		"""
		results = {}
		found = False
		
		for name, mixin in self._mixins.items():
			if hasattr(mixin, func_name):
				found = True
				func = getattr(mixin, func_name)
				if not callable(func):
					raise AttributeError(f"'{func_name}' in mixin '{name}' is not callable")
				results[name] = func(*args, **kwargs)
		
		if not found:
			raise AttributeError(f"No mixin has function '{func_name}'")
			
		return results
