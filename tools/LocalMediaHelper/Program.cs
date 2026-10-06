// LocalMediaHelper - reads the Windows System Media Transport Controls (what the volume flyout shows) and prints one JSON
// line per half second on stdout: the current session's title, artist, album, play state, position, length and a PNG of the
// cover. Commands arrive on stdin, one per line: play, pause, toggle, next, prev, seek <seconds>, select <app id> (empty = auto). Exits when stdin closes
// (the game quit). Build: tools/build_local_media_helper.ps1. Used by Assets/Scripts/UI/Phone/LocalMedia.cs.

using System.Text.Json;
using Windows.Media.Control;
using Windows.Storage.Streams;

internal static class Program
{
    private static GlobalSystemMediaTransportControlsSessionManager? _mgr;
    private static string _selected = "";   // SourceAppUserModelId to control; empty = whatever Windows treats as current
    private static string _artKey = "";
    private static string _artPath = "";
    private static int _artCounter;
    private static readonly string ArtDir = Path.Combine(Path.GetTempPath(), "HomesteaderLocalMedia");

    private static async Task Main()
    {
        Directory.CreateDirectory(ArtDir);
        foreach (string old in Directory.GetFiles(ArtDir, "art_*.png")) { try { File.Delete(old); } catch { } }

        _mgr = await GlobalSystemMediaTransportControlsSessionManager.RequestAsync();
        _ = Task.Run(ReadCommands);

        var stdout = new StreamWriter(Console.OpenStandardOutput()) { AutoFlush = true };
        while (true)
        {
            string line;
            try { line = await Snapshot(); }
            catch (Exception e) { line = JsonSerializer.Serialize(new { ok = false, error = e.Message }); }
            try { await stdout.WriteLineAsync(line); }
            catch { return; }   // the game closed the pipe
            await Task.Delay(500);
        }
    }

    private static GlobalSystemMediaTransportControlsSession? Pick()
    {
        if (_selected != "")
            foreach (var x in _mgr!.GetSessions())
                if (x.SourceAppUserModelId == _selected) return x;
        return _mgr!.GetCurrentSession();
    }

    private static async Task<string> Snapshot()
    {
        var list = new List<object>();
        foreach (var x in _mgr!.GetSessions())
        {
            string t = "";
            try { t = (await x.TryGetMediaPropertiesAsync()).Title; } catch { }
            list.Add(new { app = x.SourceAppUserModelId, title = t });
        }

        var s = Pick();
        if (s == null) return JsonSerializer.Serialize(new { ok = true, active = false, sessions = list });

        var props = await s.TryGetMediaPropertiesAsync();
        var info = s.GetPlaybackInfo();
        var tl = s.GetTimelineProperties();
        bool playing = info.PlaybackStatus == GlobalSystemMediaTransportControlsSessionPlaybackStatus.Playing;

        double pos = tl.Position.TotalSeconds;
        if (playing) pos += Math.Max(0, (DateTimeOffset.Now - tl.LastUpdatedTime).TotalSeconds);
        double len = (tl.EndTime - tl.StartTime).TotalSeconds;
        if (len > 0 && pos > len) pos = len;

        string key = props.Title + "|" + props.Artist + "|" + props.AlbumTitle;
        if (key != _artKey)
        {
            _artKey = key;
            _artPath = await SaveArt(props);
        }

        return JsonSerializer.Serialize(new
        {
            ok = true,
            active = true,
            sessions = list,
            app = s.SourceAppUserModelId,
            title = props.Title,
            artist = props.Artist,
            album = props.AlbumTitle,
            playing,
            pos,
            len,
            canSeek = info.Controls.IsPlaybackPositionEnabled && len > 0,
            art = _artPath,
        });
    }

    private static async Task<string> SaveArt(GlobalSystemMediaTransportControlsSessionMediaProperties props)
    {
        try
        {
            var thumb = props.Thumbnail;
            if (thumb == null) return "";
            using var stream = await thumb.OpenReadAsync();
            if (stream.Size == 0 || stream.Size > 8_000_000) return "";
            var reader = new DataReader(stream);
            await reader.LoadAsync((uint)stream.Size);
            var bytes = new byte[stream.Size];
            reader.ReadBytes(bytes);
            string path = Path.Combine(ArtDir, $"art_{++_artCounter}.png");
            await File.WriteAllBytesAsync(path, bytes);
            return path;
        }
        catch { return ""; }
    }

    private static async Task ReadCommands()
    {
        string? line;
        while ((line = await Console.In.ReadLineAsync()) != null)
        {
            try { await Run(line.Trim()); } catch { }
        }
        Environment.Exit(0);   // stdin closed: the game is gone
    }

    private static async Task Run(string cmd)
    {
        string[] parts = cmd.Split(' ', 2);
        if (parts[0] == "select") { _selected = parts.Length > 1 ? parts[1].Trim() : ""; _artKey = ""; return; }
        var s = _mgr == null ? null : Pick();
        if (s == null) return;
        switch (parts[0])
        {
            case "play": await s.TryPlayAsync(); break;
            case "pause": await s.TryPauseAsync(); break;
            case "toggle": await s.TryTogglePlayPauseAsync(); break;
            case "next": await s.TrySkipNextAsync(); break;
            case "prev": await s.TrySkipPreviousAsync(); break;
            case "seek":
                if (parts.Length > 1 && double.TryParse(parts[1], System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out double sec))
                    await s.TryChangePlaybackPositionAsync((long)(sec * 10_000_000));
                break;
        }
    }
}
