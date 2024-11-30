from typing import Type, Dict, List, Any
import logging
import copy

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
	
	def add_mixin(self, name: str, mixin_class: Type[Mixin], **kwargs) -> Mixin:
		"""
		Add a mixin to the mixer.
		
		Args:
			name: The attribute name to access the mixin instance
			mixin_class: The mixin class to instantiate and mix in
			**kwargs: Additional arguments passed to mix_init
		"""
		# Validate mixin
		if not isinstance(mixin_class, type) or not issubclass(mixin_class, Mixin):
			raise InvalidMixinError(f"{mixin_class.__name__} must be a subclass of Mixin")
		
		# Check for name conflicts
		if name in self._mixins:
			raise DuplicateMixinError(f"Mixin name '{name}' is already in use")
		
		logger.info(f"Adding mixin '{name}' ({mixin_class.__name__})")
		
		# Create instance
		instance = mixin_class()
		# Set mixer using the custom attribute name
		setattr(instance, f"_{instance._mixer_attr}", self)
		
		# Store the instance
		self._mixins[name] = instance
		setattr(self, name, instance)
		
		# Export methods
		for method_name in mixin_class._exports:
			if hasattr(self, method_name):
				# Track conflicts but don't export
				self._method_conflicts.setdefault(method_name, []).append(name)
				logger.warning(f"Method '{method_name}' from mixin '{name}' conflicts with existing method and was not exported")
			else:
				method = getattr(instance, method_name)
				setattr(self, method_name, method)
				logger.debug(f"Exported method '{method_name}' from mixin '{name}'")
		
		# Initialize with any provided kwargs
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
	
	def remove_all_mixins(self) -> None:
		"""Remove all mixins from the mixer."""
		logger.info("Removing all mixins")
		for name in list(self._mixins.keys()):
			self.remove_mixin(name)
	
	def __copy__(self) -> 'Mixer':
		"""Support for copy.copy()."""
		logger.debug("Creating shallow copy of Mixer")
		new_mixer = Mixer()
		
		# Copy mixins without their exported methods
		for name, mixin in self._mixins.items():
			mixin_class = mixin.__class__
			# Create a shallow copy of the mixin
			new_mixin = copy.copy(mixin)
			# Reset mixer reference to the new mixer
			setattr(new_mixin, f"_{new_mixin._mixer_attr}", new_mixer)
			# Store the mixin
			new_mixer._mixins[name] = new_mixin
			setattr(new_mixer, name, new_mixin)
			# Re-export methods
			for method_name in mixin_class._exports:
				if not hasattr(new_mixer, method_name):
					method = getattr(new_mixin, method_name)
					setattr(new_mixer, method_name, method)
		
		# Copy conflict tracking
		new_mixer._method_conflicts = copy.copy(self._method_conflicts)
		return new_mixer
	
	def __deepcopy__(self, memo: Dict[int, Any]) -> 'Mixer':
		"""Support for copy.deepcopy()."""
		logger.debug("Creating deep copy of Mixer")
		# First create a shallow copy
		new_mixer = copy.copy(self)
		# Store it in the memo to handle circular references
		memo[id(self)] = new_mixer
		
		# Now deep copy the mixins
		for name, mixin in list(new_mixer._mixins.items()):
			try:
				# Remove the mixin temporarily to avoid circular references
				delattr(new_mixer, name)
				del new_mixer._mixins[name]
				# Create deep copy of the mixin
				new_mixin = copy.deepcopy(mixin, memo)
				# Reset mixer reference
				setattr(new_mixin, f"_{new_mixin._mixer_attr}", new_mixer)
				# Store the mixin
				new_mixer._mixins[name] = new_mixin
				setattr(new_mixer, name, new_mixin)
				# Re-export methods
				for method_name in new_mixin.__class__._exports:
					if not hasattr(new_mixer, method_name):
						method = getattr(new_mixin, method_name)
						setattr(new_mixer, method_name, method)
			except Exception as e:
				logger.warning(f"Failed to deep copy mixin '{name}': {e}")
				continue
		
		# Deep copy conflict tracking
		new_mixer._method_conflicts = copy.deepcopy(self._method_conflicts, memo)
		return new_mixer
