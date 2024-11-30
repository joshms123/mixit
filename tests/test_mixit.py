import pytest
from mixit import Mixer, Mixin, export
from mixit.exceptions import (
	MixinNotFoundError,
	DuplicateMixinError,
	InvalidMixinError
)

class CounterMixin(Mixin):
	def __init__(self):
		super().__init__()
		self.value = 0
	
	@export
	def increment(self):
		self.value += 1
		return self.value
	
	@export
	def decrement(self):
		self.value -= 1
		return self.value

class MathMixin(Mixin):
	def __init__(self):
		super().__init__()
		self.last_result = 0
		self.precision = 2
	
	def mix_init(self, precision: int = 2, **kwargs):
		self.precision = precision
	
	@export
	def add(self, a: float, b: float) -> float:
		self.last_result = round(a + b, self.precision)
		return self.last_result

def test_basic_usage():
	mixer = Mixer()
	mixer.add_mixin("counter", CounterMixin)
	
	assert hasattr(mixer, "counter")
	assert hasattr(mixer, "increment")
	assert mixer.increment() == 1
	assert mixer.increment() == 2
	assert mixer.counter.value == 2

def test_mix_init():
	mixer = Mixer()
	mixer.add_mixin("math", MathMixin, precision=3)
	
	assert mixer.add(1.2345, 2.3456) == 3.58
	assert mixer.math.last_result == 3.58
	
	# Test default precision
	mixer.add_mixin("math2", MathMixin)
	assert mixer.math2.precision == 2

def test_mixin_removal():
	mixer = Mixer()
	mixer.add_mixin("temp", CounterMixin)
	
	assert hasattr(mixer, "temp")
	assert hasattr(mixer, "increment")
	
	mixer.remove_mixin("temp")
	
	assert not hasattr(mixer, "temp")
	assert not hasattr(mixer, "increment")

def test_duplicate_mixin():
	mixer = Mixer()
	mixer.add_mixin("test", CounterMixin)
	
	with pytest.raises(DuplicateMixinError):
		mixer.add_mixin("test", CounterMixin)

def test_invalid_mixin():
	mixer = Mixer()
	
	class NotAMixin:
		pass
	
	with pytest.raises(InvalidMixinError):
		mixer.add_mixin("invalid", NotAMixin)

def test_mixin_not_found():
	mixer = Mixer()
	
	with pytest.raises(MixinNotFoundError):
		mixer.get_mixin("nonexistent")
	
	with pytest.raises(MixinNotFoundError):
		mixer.remove_mixin("nonexistent")

def test_method_conflict():
	mixer = Mixer()
	mixer.add_mixin("c1", CounterMixin)
	
	class AnotherCounter(Mixin):
		@export
		def increment(self):
			return 42
	
	# Should not export conflicting method
	mixer.add_mixin("c2", AnotherCounter)
	assert mixer.increment() != 42  # Still using c1's method
	
	# Check conflict tracking
	conflicts = mixer.get_conflicts()
	assert 'increment' in conflicts
	assert 'c2' in conflicts['increment']

class LoggerMixin(Mixin):
	def __init__(self):
		super().__init__()
		self.logs = []
		self.prefix = ""
	
	def mix_init(self, prefix: str = "", **kwargs):
		self.prefix = prefix
	
	@export
	def log(self, message: str):
		self.logs.append(f"{self.prefix}{message}")
		return len(self.logs)

class CoordinatedMixin(Mixin):
	@export
	def do_work(self):
		# Access another mixin through the mixer
		logger = self.mixer.logger
		logger.log("Starting work")
		
		# Access another mixin's exported method directly
		self.mixer.log("Work in progress")
		
		# Do some work
		result = 42
		
		logger.log("Work complete")
		return result

def test_mixin_coordination():
	mixer = Mixer()
	
	# Add both mixins
	mixer.add_mixin("logger", LoggerMixin, prefix="[WORK] ")
	mixer.add_mixin("worker", CoordinatedMixin)
	
	# Use coordinated mixins
	result = mixer.do_work()
	
	# Verify coordination worked
	assert result == 42
	assert len(mixer.logger.logs) == 3
	assert mixer.logger.logs[0] == "[WORK] Starting work"
	assert mixer.logger.logs[1] == "[WORK] Work in progress"
	assert mixer.logger.logs[2] == "[WORK] Work complete"

def test_mixer_access():
	mixer = Mixer()
	mixer.add_mixin("counter", CounterMixin)
	
	# Mixin can access its mixer
	assert mixer.counter.mixer is mixer
	
	# Mixin not added to mixer should raise error
	unattached = CounterMixin()
	with pytest.raises(RuntimeError) as exc:
		_ = unattached.mixer
	assert "not attached to a mixer" in str(exc.value)

class CustomMixerMixin(Mixin, mixer_attr='container'):
	@export
	def get_value(self):
		return 42

def test_custom_mixer_attr():
	mixer = Mixer()
	mixer.add_mixin("custom", CustomMixerMixin)
	
	# Can access mixer through custom attribute
	assert mixer.custom.container is mixer
	assert not hasattr(mixer.custom, 'mixer')
	
	# Original functionality works
	assert mixer.get_value() == 42
	
	# Error still raised when not attached
	unattached = CustomMixerMixin()
	with pytest.raises(RuntimeError) as exc:
		_ = unattached.container
	assert "not attached to a mixer" in str(exc.value)

def test_add_mixin_instance():
	mixer = Mixer()
	
	# Create a mixin instance directly
	counter = CounterMixin()
	counter.value = 42  # Pre-configure the instance
	
	# Add the instance
	mixer.add_mixin_instance("counter", counter)
	
	# Verify instance was added correctly
	assert mixer.counter is counter
	assert hasattr(mixer, "increment")
	assert hasattr(mixer, "decrement")
	assert mixer.counter.value == 42
	
	# Verify methods work
	assert mixer.increment() == 43
	assert mixer.decrement() == 42
	
	# Test adding invalid instance
	class NotAMixin:
		pass
	
	with pytest.raises(InvalidMixinError):
		mixer.add_mixin_instance("invalid", NotAMixin())
	
	# Test duplicate name
	counter2 = CounterMixin()
	with pytest.raises(DuplicateMixinError):
		mixer.add_mixin_instance("counter", counter2)

def test_call_all_mixins():
	mixer = Mixer()
	
	# Test calling a method on all mixins of same type
	mixer.add_mixin("logger1", LoggerMixin, prefix="[1] ")
	mixer.add_mixin("logger2", LoggerMixin, prefix="[2] ")
	
	results = mixer.call_all_mixins("log", "test message")
	assert results == {"logger1": 1, "logger2": 1}
	assert mixer.logger1.logs == ["[1] test message"]
	assert mixer.logger2.logs == ["[2] test message"]
	
	# Test with args and kwargs
	class ConfigMixin(Mixin):
		def set_config(self, name, value=None, prefix=""):
			self.name = prefix + name
			self.value = value
			return self.name
	
	mixer.add_mixin("cfg1", ConfigMixin)
	mixer.add_mixin("cfg2", ConfigMixin)
	
	# Call method only on config mixins
	results = mixer.call_all_mixins("set_config", "test", value=42, prefix="config_")
	assert results == {"cfg1": "config_test", "cfg2": "config_test"}
	assert mixer.cfg1.value == 42
	assert mixer.cfg2.value == 42
	
	# Test with non-existent method
	with pytest.raises(AttributeError) as exc:
		mixer.call_all_mixins("nonexistent_method")
	assert "No mixin has function 'nonexistent_method'" == str(exc.value)
	
	# Test with non-callable attribute
	mixer.cfg1.test_attr = "not callable"
	with pytest.raises(AttributeError) as exc:
		mixer.call_all_mixins("test_attr")
	assert "is not callable" in str(exc.value)
