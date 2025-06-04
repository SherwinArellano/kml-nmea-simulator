# Moved Improvements

This was in the root README file and since it's cluttering it, I moved them here.

## Improvements

### [x] Event Emitter (Perhaps not needed anymore)

**Update (June 4, 2025):** In the end, I implemented events in `TrackPlayer` but when the track has started, has finished, and has repeated. As for prop-drilling, I used a singleton of `AppConfig`.

Use the event emitter (pyee) to prevent _"prop-drilling"_ `AppConfig` and to decouple classes from other classes. For example, `TrackPlayer` is getting passed `AppConfig` just because it needs the `AppConfig.nmea_types` global configuration.

There are of course other solutions which mitigate this:

1. To create a root parent class which all classes will inherit and has the global configuration. **Problem:** Ties everything to a grand parent class which creates a very coupled system.
2. Use a Singleton. **Problem:** Methods become _unpure_ in the sense that they depend on the outside code.

By using an event emitter, the problems above are solved quite nicely:

```py
@evented # notice this helper from pyee
class TrackPlayer(ABC):
    def __init__(): ...

    @abstractmethod
    async def play(self): ...

    # we can also use decorators for these on_events
    # e.g. @trackPlayer.on_presend()
    def on_presend(self, handler): ...

    def on_finished(self, handler): ...
```

**Update (May 29, 2025):** Perhaps not needed at all and just added architectural complexity.

### [x] ~~Remove AppConfig~~

As it stands, app config is a god object which I want to avoid after thinking about it. In the sense that it creates this sense of obligation that I have to depend on it too much and pass it anywhere it's needed. Also, there's the overhead of adding a new argument for the cli also means maintaining `AppConfig`. And so I decided in the future to remove it.

As for what will happen to classes that do depend on it, look at the `core.utils.call_context` module for inspiration, also check event emitter, and always think: Single Responsibility Principle, i.e., _does this class really need to be coupled with this other class?_ Think in components, think in composition.

**Update (May 29, 2025):** Okay so trying to inject this everywhere and decoupling its components just lead to more architecture complexity and dependency indirection. I made it instead a Singleton which classes can use globally if they need the global App configuration. It breaks the impurity of methods but it maintains the simplicity and maintainability of code.
