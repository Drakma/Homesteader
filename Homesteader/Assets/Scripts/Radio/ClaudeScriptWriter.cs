// ClaudeScriptWriter.cs - the optional live script writer: sends the day's fact sheet (RadioScriptContext) and the
// station's persona to the Claude API (POST https://api.anthropic.com/v1/messages, raw HTTP through UnityWebRequest
// because the Anthropic SDK is not a Unity package) and parses the returned dialogue into a RadioEpisode. Any failure
// (no key, network, refusal, unparseable reply) reports an error and RadioPlayer falls back to the templated writer.
// The model only ever sees the fact sheet: no save data, no file paths, nothing from outside the fact sheet.

using System;
using System.Collections;
using System.Collections.Generic;
using System.Text;
using Homesteader.Modding;
using UnityEngine;
using UnityEngine.Networking;

namespace Homesteader.Radio
{
    public static class ClaudeScriptWriter
    {
        private const string Endpoint = "https://api.anthropic.com/v1/messages";
        private const string ApiVersion = "2023-06-01";
        private const string FallbackBeta = "server-side-fallback-2026-07-01";
        private const int TimeoutSeconds = 90;

        /// <summary>Coroutine: writes an episode with Claude. Exactly one of onDone / onError is called.</summary>
        public static IEnumerator Write(RadioStationDefinition station, RadioScriptContext ctx, Action<RadioEpisode> onDone, Action<string> onError)
        {
            string key = RadioSettings.ApiKey;
            if (string.IsNullOrEmpty(key)) { onError?.Invoke("No Claude API key set (Settings > Audio > Radio)."); yield break; }

            string body = BuildRequestBody(station, ctx);
            using (var req = new UnityWebRequest(Endpoint, UnityWebRequest.kHttpVerbPOST))
            {
                req.uploadHandler = new UploadHandlerRaw(Encoding.UTF8.GetBytes(body));
                req.downloadHandler = new DownloadHandlerBuffer();
                req.timeout = TimeoutSeconds;
                req.SetRequestHeader("content-type", "application/json");
                req.SetRequestHeader("x-api-key", key);
                req.SetRequestHeader("anthropic-version", ApiVersion);
                req.SetRequestHeader("anthropic-beta", FallbackBeta);

                yield return req.SendWebRequest();

                string text = req.downloadHandler != null ? req.downloadHandler.text : "";
                if (req.result != UnityWebRequest.Result.Success)
                {
                    string detail = ExtractApiError(text);
                    onError?.Invoke($"Claude request failed ({(int)req.responseCode} {req.error}){(string.IsNullOrEmpty(detail) ? "" : ": " + detail)}");
                    yield break;
                }

                if (!ModJson.TryParse(text, out ModJsonValue root, out string jsonError))
                {
                    onError?.Invoke("Claude reply was not JSON: " + jsonError);
                    yield break;
                }

                string stop = root.Get("stop_reason").AsString("");
                if (stop == "refusal")
                {
                    onError?.Invoke("Claude declined to write this episode (" + root.Get("stop_details").Get("category").AsString("refusal") + ").");
                    yield break;
                }

                var sb = new StringBuilder();
                foreach (ModJsonValue block in root.Get("content").Items)
                    if (block.Get("type").AsString("") == "text") sb.Append(block.Get("text").AsString(""));

                RadioEpisode ep = ParseEpisode(sb.ToString(), station, ctx, out string parseError);
                if (ep == null) { onError?.Invoke(parseError); yield break; }
                if (stop == "max_tokens") ep.lines.Add(new RadioLine { speaker = station.Speakers[0].Id, text = "And that's all we have time for today." });
                onDone?.Invoke(ep);
            }
        }

        // ------------------------------------------------------------------ request

        public static string SystemPrompt(RadioStationDefinition station)
        {
            var sb = new StringBuilder();
            sb.AppendLine("You write the script for one episode of a radio programme inside a homesteading video game. The player listens to it on their in-game phone.");
            sb.AppendLine();
            sb.AppendLine("Programme: " + station.Name + (string.IsNullOrEmpty(station.Frequency) ? "" : " on " + station.Frequency) + ".");
            if (!string.IsNullOrEmpty(station.Tagline)) sb.AppendLine("Tagline: " + station.Tagline);
            if (!string.IsNullOrEmpty(station.Persona)) sb.AppendLine("Character: " + station.Persona);
            sb.AppendLine("Speakers (use exactly these ids):");
            foreach (RadioSpeaker s in station.Speakers)
                sb.AppendLine($"  {s.Id} = {s.Name}" + (string.IsNullOrEmpty(s.Style) ? "" : $" ({s.Style})"));
            sb.AppendLine("Segments, in order: " + string.Join(", ", station.Segments) + ".");
            sb.AppendLine($"Length: about {Mathf.RoundToInt(station.EpisodeMinutes * 130f)} words in total, spoken at a natural pace.");
            sb.AppendLine();
            sb.AppendLine("Rules:");
            sb.AppendLine("- Use only the facts given. Do not invent places, people, events, prices, or weather that is not in the facts. If a fact is missing, leave it out.");
            sb.AppendLine("- The text will be read aloud by a text-to-speech voice: write numbers and times the way they are spoken, no abbreviations, no symbols, no stage directions, no emoji, no markdown.");
            sb.AppendLine("- Temperatures are already in the player's units; say them as plain degrees.");
            sb.AppendLine("- The hosts talk to each other and to the listener. Keep it warm and practical, with light humour; never mention being an AI or a game.");
            sb.AppendLine("- Output ONLY a JSON array of objects with keys \"speaker\" and \"text\", one object per spoken turn, no other text before or after it.");
            return sb.ToString();
        }

        private static string BuildRequestBody(RadioStationDefinition station, RadioScriptContext ctx)
        {
            var sb = new StringBuilder();
            sb.Append('{');
            sb.Append("\"model\":").Append(Quote(RadioSettings.Model)).Append(',');
            sb.Append("\"max_tokens\":4000,");
            sb.Append("\"output_config\":{\"effort\":\"low\"},");
            sb.Append("\"fallbacks\":\"default\",");
            sb.Append("\"system\":").Append(Quote(SystemPrompt(station))).Append(',');
            sb.Append("\"messages\":[{\"role\":\"user\",\"content\":")
              .Append(Quote("Today's facts:\n\n" + ctx.ToFactSheet() + "\nWrite today's episode."))
              .Append("}]");
            sb.Append('}');
            return sb.ToString();
        }

        // ------------------------------------------------------------------ response

        private static RadioEpisode ParseEpisode(string text, RadioStationDefinition station, RadioScriptContext ctx, out string error)
        {
            error = null;
            int start = text.IndexOf('[');
            int end = text.LastIndexOf(']');
            if (start < 0 || end <= start) { error = "Claude reply held no JSON array."; return null; }
            string json = text.Substring(start, end - start + 1);
            if (!ModJson.TryParse(json, out ModJsonValue arr, out string jsonError) || !arr.IsArray)
            {
                error = "Claude script was not a JSON array: " + jsonError;
                return null;
            }

            var ep = new RadioEpisode
            {
                stationId = station.Id,
                dayOfYear = ctx.DayOfYear,
                worldSeed = ctx.WorldSeed,
                title = $"{station.Name}: {ctx.Weekday}, {ctx.MonthName} {ctx.DayOfMonth}",
                source = "claude",
            };
            foreach (ModJsonValue turn in arr.Items)
            {
                if (!turn.IsObject) continue;
                string speaker = turn.Get("speaker").AsString("");
                string line = CleanForSpeech(turn.Get("text").AsString(""));
                if (line.Length == 0) continue;
                RadioSpeaker s = station.FindSpeaker(speaker);
                ep.lines.Add(new RadioLine { speaker = s != null ? s.Id : station.Speakers[0].Id, text = line });
            }
            if (ep.lines.Count == 0) { error = "Claude script had no spoken lines."; return null; }
            return ep;
        }

        /// <summary>Strips anything a TTS voice would read badly: markdown, bracketed stage directions, stray symbols.</summary>
        private static string CleanForSpeech(string s)
        {
            if (string.IsNullOrEmpty(s)) return "";
            s = System.Text.RegularExpressions.Regex.Replace(s, @"\[[^\]]*\]|\([^)]*\)", " ");   // [laughs] (pause)
            s = s.Replace("*", "").Replace("#", "").Replace("`", "").Replace("_", " ");
            s = System.Text.RegularExpressions.Regex.Replace(s, @"\s{2,}", " ");
            return s.Trim();
        }

        private static string ExtractApiError(string body)
        {
            if (string.IsNullOrEmpty(body)) return "";
            if (ModJson.TryParse(body, out ModJsonValue root, out _))
                return root.Get("error").Get("message").AsString("");
            return body.Length > 200 ? body.Substring(0, 200) : body;
        }

        // ------------------------------------------------------------------ json

        public static string Quote(string s)
        {
            var sb = new StringBuilder(s.Length + 2);
            sb.Append('"');
            foreach (char c in s)
            {
                switch (c)
                {
                    case '"': sb.Append("\\\""); break;
                    case '\\': sb.Append("\\\\"); break;
                    case '\n': sb.Append("\\n"); break;
                    case '\r': sb.Append("\\r"); break;
                    case '\t': sb.Append("\\t"); break;
                    default:
                        if (c < 0x20) sb.Append("\\u").Append(((int)c).ToString("x4"));
                        else sb.Append(c);
                        break;
                }
            }
            sb.Append('"');
            return sb.ToString();
        }
    }
}
