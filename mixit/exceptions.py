class MixinError(Exception):
	"""Base exception for all mixin-related errors."""

class MixinNotFoundError(MixinError):
	"""Raised when attempting to access a mixin that hasn't been added."""

class MixinMethodError(MixinError):
	"""Raised when there's an error with mixin method handling."""

class DuplicateMixinError(MixinError):
	"""Raised when attempting to add a mixin with a name that's already in use."""

class InvalidMixinError(MixinError):
	"""Raised when attempting to add an invalid mixin."""
