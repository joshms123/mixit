import pytest
from mixit import Mixer, Mixin, export, derive_mixin_name
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

class BaseHandlerMixin(Mixin, export_prefix="handle_"):
        def handle_base(self):
                return "base"
        
        def other_method(self):
                return "not exported"

class SpecializedHandlerMixin(BaseHandlerMixin):
        def handle_special(self):
                return "special"
        
        def another_method(self):
                return "not exported"

class DifferentHandlerMixin(BaseHandlerMixin, export_prefix="process_"):
        def handle_something(self):
                return "not exported"
        
        def process_data(self):
                return "processed"

class MixedMixin(Mixin):
        @export
        def explicit_export(self):
                return "explicit"
        
        def not_exported(self):
                return "not exported"

def test_auto_export():
        mixer = Mixer()
        
        # Test base mixin with auto-export prefix
        mixer.add_mixin("base", BaseHandlerMixin)
        assert hasattr(mixer, "handle_base")
        assert not hasattr(mixer, "other_method")
        assert mixer.handle_base() == "base"
        
        # Test inherited auto-export prefix
        mixer.add_mixin("special", SpecializedHandlerMixin)
        assert hasattr(mixer, "handle_special")
        assert not hasattr(mixer, "another_method")
        assert mixer.handle_special() == "special"
        assert mixer.special.handle_base() == "base"  # Inherited method
        
        # Test overridden prefix
        mixer.add_mixin("different", DifferentHandlerMixin)
        assert hasattr(mixer, "process_data")
        assert not hasattr(mixer, "handle_something")
        assert mixer.process_data() == "processed"
        
        # Test mixed explicit and auto exports
        mixer.add_mixin("mixed", MixedMixin)
        assert hasattr(mixer, "explicit_export")
        assert not hasattr(mixer, "not_exported")
        assert mixer.explicit_export() == "explicit"

def test_auto_export_conflicts():
        mixer = Mixer()
        
        # Add base handler
        mixer.add_mixin("handler1", BaseHandlerMixin)
        assert mixer.handle_base() == "base"
        
        # Add another handler with same prefix - should create conflict
        class AnotherHandler(Mixin, export_prefix="handle_"):
                def handle_base(self):
                        return "another"
        
        mixer.add_mixin("handler2", AnotherHandler)
        
        # Original method should still be used
        assert mixer.handle_base() == "base"
        
        # Conflict should be tracked
        conflicts = mixer.get_conflicts()
        assert "handle_base" in conflicts
        assert "handler2" in conflicts["handle_base"]

def test_auto_export_inheritance_chain():
        mixer = Mixer()
        
        # Test deeper inheritance chain
        class Level1(BaseHandlerMixin):
                def handle_level1(self):
                        return "level1"
        
        class Level2(Level1):
                def handle_level2(self):
                        return "level2"
        
        class Level3(Level2, export_prefix="new_"):
                def handle_old(self):
                        return "not exported"
                
                def new_method(self):
                        return "new"
        
        # Test Level2 (inherits prefix)
        mixer.add_mixin("l2", Level2)
        assert hasattr(mixer, "handle_base")  # from base
        assert hasattr(mixer, "handle_level1")  # from level1
        assert hasattr(mixer, "handle_level2")  # from level2
        
        # Test Level3 (overrides prefix)
        mixer.add_mixin("l3", Level3)
        assert hasattr(mixer, "new_method")
        assert not hasattr(mixer, "handle_old")

def test_derive_mixin_name():
        class SimpleDialogMixin(Mixin):
                pass

        class ConfigMixin(Mixin):
                pass

        class MastodonTimelineSubhandler(Mixin):
                pass

        class XMLParser(Mixin):
                pass

        class GUIAPI(Mixin):
                pass

        assert derive_mixin_name(SimpleDialogMixin) == "simple_dialog_mixin"
        assert derive_mixin_name(ConfigMixin) == "config_mixin"
        assert derive_mixin_name(MastodonTimelineSubhandler) == "mastodon_timeline_subhandler"
        assert derive_mixin_name(XMLParser) == "xml_parser"
        assert derive_mixin_name(GUIAPI) == "guiapi"

def test_add_mixin_class_only():
        mixer = Mixer()
        mixer.add_mixin(CounterMixin)

        # Name is auto-derived as "counter_mixin"
        assert hasattr(mixer, "counter_mixin")
        assert hasattr(mixer, "increment")
        assert mixer.increment() == 1

def test_add_mixin_class_only_with_kwargs():
        mixer = Mixer()
        mixer.add_mixin(MathMixin, precision=3)

        assert hasattr(mixer, "math_mixin")
        assert mixer.math_mixin.precision == 3
        assert mixer.add(1.2345, 2.3456) == 3.58

def test_add_mixin_explicit_name_still_works():
        mixer = Mixer()
        mixer.add_mixin("counter", CounterMixin)

        assert hasattr(mixer, "counter")
        assert not hasattr(mixer, "counter_mixin")
        assert mixer.increment() == 1

def test_add_mixin_invalid_first_arg():
        mixer = Mixer()
        with pytest.raises(InvalidMixinError):
                mixer.add_mixin(42)

def test_add_mixin_string_without_class():
        mixer = Mixer()
        with pytest.raises(InvalidMixinError):
                mixer.add_mixin("name")

def test_add_mixin_class_and_kwarg_class_conflict():
        mixer = Mixer()
        with pytest.raises(InvalidMixinError):
                mixer.add_mixin(CounterMixin, mixin_class=MathMixin)

def test_add_mixin_instance_instance_only():
        mixer = Mixer()
        counter = CounterMixin()
        counter.value = 7
        mixer.add_mixin_instance(counter)

        assert hasattr(mixer, "counter_mixin")
        assert mixer.counter_mixin is counter
        assert mixer.increment() == 8

def test_add_mixin_instance_explicit_name_still_works():
        mixer = Mixer()
        counter = CounterMixin()
        mixer.add_mixin_instance("counter", counter)

        assert hasattr(mixer, "counter")
        assert not hasattr(mixer, "counter_mixin")

def test_add_mixins_variadic():
        class MixinA(Mixin):
                pass

        class MixinB(Mixin):
                pass

        class MixinC(Mixin):
                pass

        mixer = Mixer()
        instances = mixer.add_mixins(MixinA, MixinB, MixinC)

        # All registered with auto-derived names
        assert hasattr(mixer, "mixin_a")
        assert hasattr(mixer, "mixin_b")
        assert hasattr(mixer, "mixin_c")

        # Instances returned in input order
        assert len(instances) == 3
        assert isinstance(instances[0], MixinA)
        assert isinstance(instances[1], MixinB)
        assert isinstance(instances[2], MixinC)

        # Mixer's _mixins dict preserves registration order (Python 3.7+)
        assert list(mixer.get_mixins().keys()) == ["mixin_a", "mixin_b", "mixin_c"]

def test_add_mixins_empty():
        mixer = Mixer()
        instances = mixer.add_mixins()
        assert instances == []

def test_add_mixins_invalid_class():
        mixer = Mixer()

        class NotAMixin:
                pass

        with pytest.raises(InvalidMixinError):
                mixer.add_mixins(NotAMixin)

def test_add_mixins_preserves_order_around_kwargs_call():
        # Pattern from real usage: bulk-add some plain mixins, then add a parameterized
        # one with add_mixin, then bulk-add more.
        class First(Mixin):
                pass

        class Second(Mixin):
                pass

        class WithKwargs(Mixin):
                def mix_init(self, value=0, **kwargs):
                        self.value = value

        class Third(Mixin):
                pass

        mixer = Mixer()
        mixer.add_mixins(First, Second)
        mixer.add_mixin(WithKwargs, value=42)
        mixer.add_mixins(Third)

        assert list(mixer.get_mixins().keys()) == ["first", "second", "with_kwargs", "third"]
        assert mixer.with_kwargs.value == 42

def test_mixed_export_methods():
        mixer = Mixer()
        
        # Test mixing @export with auto-export prefix
        class MixedExportMixin(Mixin, export_prefix="handle_"):
                def handle_auto(self):
                        return "auto exported"
                
                @export
                def explicit_method(self):
                        return "explicitly exported"
                
                @export
                def handle_both(self):
                        return "both ways"
                
                def normal_method(self):
                        return "not exported"
        
        mixer.add_mixin("mixed", MixedExportMixin)
        
        # Auto-exported method
        assert hasattr(mixer, "handle_auto")
        assert mixer.handle_auto() == "auto exported"
        
        # Explicitly exported method
        assert hasattr(mixer, "explicit_method")
        assert mixer.explicit_method() == "explicitly exported"
        
        # Method that matches prefix and has @export
        assert hasattr(mixer, "handle_both")
        assert mixer.handle_both() == "both ways"
        assert "handle_both" in mixer.mixed.__class__._exports
        assert mixer.mixed.__class__._exports.count("handle_both") == 1  # Should only appear once
        
        # Non-exported method
        assert not hasattr(mixer, "normal_method")
