Let's see... If we have an InstantPlayer, the FileTransport must have two options: `single` or `multi`.

InstantPlayer does not care about the repeat option. Though it does care about the loop option.

If `single` then perhaps the FileTransport is divided also into two classes? One SingleFileTransport and another MultiFileTransport? Like basically, SingleFileTransport will contain the array of all timestamp-ordered messages and after it finishes processing all tracks, it saves the file. But when do we know that all tracks have finished processing? Perhaps, InstantPlayer has this very option where it invokes some sort of completed event. (Likely a method.) Or maybe not, we can just call SingleFileTransport.save() or something after InstantPlayer.play().

**Motivation:** As to why I am doing this is because currently, file generation and simulation are two different distinct classes. Like they pretty much share the same "idea" logic, just implemented differently and have different options. Also, this way, everything is handled by the loader. (Might just become a main.py integrating both the loader and the cli.py) To be honest, I was fine with the different classes approach but then I realized, I would need to pass AppConfig to the FileGenerator class whereas that was already handled before the TrackPlayer.
