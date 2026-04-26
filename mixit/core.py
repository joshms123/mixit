from typing import Type, Dict, List, Any, Union
import logging
import re

from .base import Mixin
from .exceptions import (
	MixinNotFoundError,
	DuplicateMixinError,
	InvalidMixinError
)

logger = logging.getLogger(__name__)

_CAMEL_RE_1 = re.compile(r'(.)([A-Z][a-z]+)')
_CAMEL_RE_2 = re.compile(r'([a-z0-9])([A-Z])')

def derive_mixin_name(cls: Type[Mixin]) -> str:
	"""Convert a mixin class name to snake_case for use as a registration key.

	Examples:
		SimpleDialogMixin  -> simple_dialog_mixin
		ConfigMixin        -> config_mixin
		XMLParser          -> xml_parser
		GUIAPI             -> guiapi
	"""
	name = cls.__name__
	name = _CAMEL_RE_1.sub(r'\1_\2', name)
	name = _CAMEL_RE_2.sub(r'\1_\2', name).lower()
	return name

class Mixer:
	"""
	A central mixer that manages mixins and their exported methods.
	"""
	def __init__(self):
		self._mixins: Dict[str, Mixin] = {}
		self._method_conflicts: Dict[str, List[str]] = {}
		logger.info("Initialized new Mixer instance")
	
	def add_mixin_instance(self, instance_or_name: Union[Mixin, str], instance: Mixin = None) -> Mixin:
		"""
		Add an existing mixin instance to the mixer.

		Two call forms are supported:
			add_mixin_instance(instance)               # name derived from instance.__class__.__name__
			add_mixin_instance("name", instance)       # explicit name

		Args:
			instance_or_name: Either a Mixin instance (name auto-derived) or a string name.
			instance: The mixin instance to add (required when first arg is a string).

		Returns:
			The added mixin instance

		Raises:
			InvalidMixinError: If instance is not a Mixin instance, or args are inconsistent.
			DuplicateMixinError: If name is already in use
		"""
		if isinstance(instance_or_name, Mixin):
			if instance is not None:
				raise InvalidMixinError("Cannot pass both an instance as first arg and an instance keyword")
			instance = instance_or_name
			name = derive_mixin_name(instance.__class__)
		elif isinstance(instance_or_name, str):
			name = instance_or_name
			if instance is None:
				raise InvalidMixinError("instance is required when a name is provided")
		else:
			raise InvalidMixinError(f"First argument must be a Mixin instance or a string, got {type(instance_or_name).__name__}")

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
	
	def add_mixin(self, mixin_or_name: Union[Type[Mixin], str], mixin_class: Type[Mixin] = None, **kwargs) -> Mixin:
		"""
		Create and add a mixin instance to the mixer.

		Two call forms are supported:
			add_mixin(MixinClass, **kwargs)           # name derived from MixinClass.__name__
			add_mixin("name", MixinClass, **kwargs)   # explicit name

		Args:
			mixin_or_name: Either a Mixin subclass (name auto-derived) or a string name.
			mixin_class: The mixin class to instantiate (required when first arg is a string).
			**kwargs: Additional arguments passed to mix_init

		Returns:
			The created and added mixin instance

		Raises:
			InvalidMixinError: If mixin_class is not a Mixin subclass, or args are inconsistent.
			DuplicateMixinError: If name is already in use
		"""
		if isinstance(mixin_or_name, type) and issubclass(mixin_or_name, Mixin):
			if mixin_class is not None:
				raise InvalidMixinError("Cannot pass both a class as first arg and a mixin_class keyword")
			mixin_class = mixin_or_name
			name = derive_mixin_name(mixin_class)
		elif isinstance(mixin_or_name, str):
			name = mixin_or_name
			if mixin_class is None:
				raise InvalidMixinError("mixin_class is required when a name is provided")
			if not isinstance(mixin_class, type) or not issubclass(mixin_class, Mixin):
				raise InvalidMixinError(f"{mixin_class.__name__} must be a subclass of Mixin")
		else:
			raise InvalidMixinError(f"First argument must be a Mixin subclass or a string, got {type(mixin_or_name).__name__}")

		logger.debug(f"Creating mixin instance of {mixin_class.__name__}")

		# Create instance
		instance = mixin_class()

		# Add the instance and initialize it
		self.add_mixin_instance(name, instance)
		instance.mix_init(**kwargs)

		return instance

	def add_mixins(self, *mixin_classes: Type[Mixin]) -> List[Mixin]:
		"""
		Add multiple mixins in order, each with an auto-derived name and no mix_init kwargs.

		Convenience for the common case of registering several plain mixins back-to-back.
		For mixins that need kwargs, call add_mixin individually around the add_mixins call
		so that registration order is preserved.

		Args:
			*mixin_classes: One or more Mixin subclasses, in the order they should register.

		Returns:
			List of created instances in the same order as the input.

		Raises:
			InvalidMixinError: If any argument is not a Mixin subclass.
			DuplicateMixinError: If a derived name is already in use.
		"""
		return [self.add_mixin(cls) for cls in mixin_classes]

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
