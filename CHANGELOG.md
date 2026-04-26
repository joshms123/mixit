# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.7.0] - 2026-04-26

### Added

- `derive_mixin_name(cls)` helper that converts a class name to snake_case for use as a registration key. Exported from the top-level `mixit` package.
- `Mixer.add_mixin` now accepts a Mixin subclass as its first argument; the registration name is auto-derived. The original `add_mixin("name", MixinClass, **kwargs)` form is unchanged.
- `Mixer.add_mixin_instance` now accepts a Mixin instance as its first argument; the registration name is auto-derived from `instance.__class__.__name__`. The original `add_mixin_instance("name", instance)` form is unchanged.
- `Mixer.add_mixins(*classes)` — variadic helper for registering several plain mixins back-to-back. Each class is added in order with an auto-derived name and no `mix_init` kwargs. Returns the list of created instances.

### Notes

- All changes are backward compatible. Existing code that passes explicit names continues to work unchanged.
- For mixins that need `mix_init` kwargs, continue using `add_mixin(MixinClass, **kwargs)` (positional class form) or the original `add_mixin("name", MixinClass, **kwargs)` form.

## [0.6.0]

### Added

- Initial public release with `Mixer`, `Mixin`, `@export`, `add_mixin_instance`, `call_all_mixins`, customisable `mixer_attr`, and auto-export prefix support.
