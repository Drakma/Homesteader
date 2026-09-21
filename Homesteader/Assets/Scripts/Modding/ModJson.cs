using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text;

namespace Homesteader.Modding
{
    /// <summary>
    /// Minimal, dependency-free JSON reader used by the mod system.
    ///
    /// We deliberately avoid Unity's JsonUtility here: mod manifests carry
    /// arbitrary, mod-author-defined shapes (per-type payload blocks, nested
    /// arrays of objects, unknown keys), which JsonUtility cannot model without
    /// a hand-written concrete class per mod type. This parser keeps the mod
    /// format open-ended so third-party content is never rejected just because
    /// the core game never anticipated its structure.
    ///
    /// Supports: objects, arrays, strings (with escapes + \uXXXX), numbers,
    /// true/false/null. Numbers are exposed as double; use the typed helpers.
    /// </summary>
    public static class ModJson
    {
        /// <summary>
        /// Parses a JSON document into a ModJsonValue tree.
        /// Throws ModJsonException with a byte offset on malformed input.
        /// </summary>
        public static ModJsonValue Parse(string text)
        {
            if (string.IsNullOrEmpty(text))
                throw new ModJsonException("Empty JSON document.");

            int index = 0;
            SkipWhitespace(text, ref index);
            ModJsonValue value = ParseValue(text, ref index);
            SkipWhitespace(text, ref index);

            if (index < text.Length)
                throw new ModJsonException($"Unexpected trailing content at offset {index}.");

            return value;
        }

        /// <summary>Non-throwing parse. Returns false and reports the error.</summary>
        public static bool TryParse(string text, out ModJsonValue value, out string error)
        {
            try
            {
                value = Parse(text);
                error = null;
                return true;
            }
            catch (Exception ex)
            {
                value = null;
                error = ex.Message;
                return false;
            }
        }

        private static ModJsonValue ParseValue(string s, ref int i)
        {
            SkipWhitespace(s, ref i);
            if (i >= s.Length)
                throw new ModJsonException($"Unexpected end of input at offset {i}.");

            char c = s[i];
            switch (c)
            {
                case '{': return ParseObject(s, ref i);
                case '[': return ParseArray(s, ref i);
                case '"': return ModJsonValue.NewString(ParseString(s, ref i));
                case 't':
                    Expect(s, ref i, "true");
                    return ModJsonValue.NewBool(true);
                case 'f':
                    Expect(s, ref i, "false");
                    return ModJsonValue.NewBool(false);
                case 'n':
                    Expect(s, ref i, "null");
                    return ModJsonValue.NewNull();
                default:
                    if (c == '-' || (c >= '0' && c <= '9'))
                        return ModJsonValue.NewNumber(ParseNumber(s, ref i));
                    throw new ModJsonException($"Unexpected character '{c}' at offset {i}.");
            }
        }

        private static ModJsonValue ParseObject(string s, ref int i)
        {
            var map = new Dictionary<string, ModJsonValue>(StringComparer.Ordinal);
            i++; // consume '{'
            SkipWhitespace(s, ref i);

            if (i < s.Length && s[i] == '}')
            {
                i++;
                return ModJsonValue.NewObject(map);
            }

            while (true)
            {
                SkipWhitespace(s, ref i);
                if (i >= s.Length || s[i] != '"')
                    throw new ModJsonException($"Expected object key string at offset {i}.");

                string key = ParseString(s, ref i);
                SkipWhitespace(s, ref i);

                if (i >= s.Length || s[i] != ':')
                    throw new ModJsonException($"Expected ':' after key '{key}' at offset {i}.");
                i++;

                ModJsonValue value = ParseValue(s, ref i);
                map[key] = value;

                SkipWhitespace(s, ref i);
                if (i >= s.Length)
                    throw new ModJsonException($"Unterminated object at offset {i}.");

                if (s[i] == ',')
                {
                    i++;
                    continue;
                }
                if (s[i] == '}')
                {
                    i++;
                    return ModJsonValue.NewObject(map);
                }
                throw new ModJsonException($"Expected ',' or '}}' at offset {i}.");
            }
        }

        private static ModJsonValue ParseArray(string s, ref int i)
        {
            var list = new List<ModJsonValue>();
            i++; // consume '['
            SkipWhitespace(s, ref i);

            if (i < s.Length && s[i] == ']')
            {
                i++;
                return ModJsonValue.NewArray(list);
            }

            while (true)
            {
                list.Add(ParseValue(s, ref i));
                SkipWhitespace(s, ref i);

                if (i >= s.Length)
                    throw new ModJsonException($"Unterminated array at offset {i}.");

                if (s[i] == ',')
                {
                    i++;
                    continue;
                }
                if (s[i] == ']')
                {
                    i++;
                    return ModJsonValue.NewArray(list);
                }
                throw new ModJsonException($"Expected ',' or ']' at offset {i}.");
            }
        }

        private static string ParseString(string s, ref int i)
        {
            i++; // consume opening quote
            var sb = new StringBuilder();

            while (i < s.Length)
            {
                char c = s[i++];
                if (c == '"')
                    return sb.ToString();

                if (c == '\\')
                {
                    if (i >= s.Length)
                        break;
                    char esc = s[i++];
                    switch (esc)
                    {
                        case '"': sb.Append('"'); break;
                        case '\\': sb.Append('\\'); break;
                        case '/': sb.Append('/'); break;
                        case 'b': sb.Append('\b'); break;
                        case 'f': sb.Append('\f'); break;
                        case 'n': sb.Append('\n'); break;
                        case 'r': sb.Append('\r'); break;
                        case 't': sb.Append('\t'); break;
                        case 'u':
                            if (i + 4 > s.Length)
                                throw new ModJsonException($"Truncated \\u escape at offset {i}.");
                            string hex = s.Substring(i, 4);
                            if (!ushort.TryParse(hex, NumberStyles.HexNumber, CultureInfo.InvariantCulture, out ushort code))
                                throw new ModJsonException($"Invalid \\u escape '{hex}' at offset {i}.");
                            sb.Append((char)code);
                            i += 4;
                            break;
                        default:
                            throw new ModJsonException($"Invalid escape '\\{esc}' at offset {i - 1}.");
                    }
                }
                else
                {
                    sb.Append(c);
                }
            }

            throw new ModJsonException("Unterminated string literal.");
        }

        private static double ParseNumber(string s, ref int i)
        {
            int start = i;
            while (i < s.Length)
            {
                char c = s[i];
                if (c == '-' || c == '+' || c == '.' || c == 'e' || c == 'E' || (c >= '0' && c <= '9'))
                    i++;
                else
                    break;
            }

            string token = s.Substring(start, i - start);
            if (!double.TryParse(token, NumberStyles.Float, CultureInfo.InvariantCulture, out double result))
                throw new ModJsonException($"Invalid number '{token}' at offset {start}.");
            return result;
        }

        private static void Expect(string s, ref int i, string literal)
        {
            if (i + literal.Length > s.Length || s.Substring(i, literal.Length) != literal)
                throw new ModJsonException($"Expected '{literal}' at offset {i}.");
            i += literal.Length;
        }

        private static void SkipWhitespace(string s, ref int i)
        {
            while (i < s.Length)
            {
                char c = s[i];
                if (char.IsWhiteSpace(c))
                    i++;
                else
                    break;
            }
        }
    }

    public class ModJsonException : Exception
    {
        public ModJsonException(string message) : base(message) { }
    }

    /// <summary>
    /// A parsed JSON node. Immutable; construct via the static factories.
    /// Typed accessors return defaults instead of throwing so mod content that
    /// omits optional fields degrades gracefully rather than aborting a load.
    /// </summary>
    public sealed class ModJsonValue
    {
        public enum NodeType { Null, Bool, Number, String, Array, Object }

        public NodeType Type { get; private set; }
        public bool BoolValue { get; private set; }
        public double NumberValue { get; private set; }
        public string StringValue { get; private set; }
        public IReadOnlyList<ModJsonValue> ArrayValue { get; private set; }
        public IReadOnlyDictionary<string, ModJsonValue> ObjectValue { get; private set; }

        private ModJsonValue() { }

        public static ModJsonValue NewNull() => new ModJsonValue { Type = NodeType.Null };
        public static ModJsonValue NewBool(bool v) => new ModJsonValue { Type = NodeType.Bool, BoolValue = v };
        public static ModJsonValue NewNumber(double v) => new ModJsonValue { Type = NodeType.Number, NumberValue = v };
        public static ModJsonValue NewString(string v) => new ModJsonValue { Type = NodeType.String, StringValue = v };
        public static ModJsonValue NewArray(List<ModJsonValue> v) => new ModJsonValue { Type = NodeType.Array, ArrayValue = v };
        public static ModJsonValue NewObject(Dictionary<string, ModJsonValue> v) => new ModJsonValue { Type = NodeType.Object, ObjectValue = v };

        public bool IsObject => Type == NodeType.Object;
        public bool IsArray => Type == NodeType.Array;
        public bool IsNull => Type == NodeType.Null;

        public bool Has(string key) =>
            Type == NodeType.Object && ObjectValue.ContainsKey(key);

        /// <summary>
        /// Child node, or null when missing / not an object.
        /// Callers that chain accessors must use <see cref="Get"/> instead, since
        /// calling an instance method on this null result would throw.
        /// </summary>
        public ModJsonValue this[string key]
        {
            get
            {
                if (Type != NodeType.Object) return null;
                return ObjectValue.TryGetValue(key, out var v) ? v : null;
            }
        }

        /// <summary>
        /// Null-safe child accessor: always returns a usable node, never null.
        /// Use this whenever you chain accessors or read optional fields
        /// (e.g. root.Get("name").AsString()), so a mod that omits a field
        /// degrades to a default instead of throwing a NullReferenceException.
        /// </summary>
        public ModJsonValue Get(string key) => this[key] ?? Null;

        /// <summary>A shared empty node returned for missing keys.</summary>
        public static readonly ModJsonValue Null = NewNull();

        public int Count => Type == NodeType.Array ? ArrayValue.Count : 0;

        public IEnumerable<ModJsonValue> Items =>
            Type == NodeType.Array ? ArrayValue : (IEnumerable<ModJsonValue>)Array.Empty<ModJsonValue>();

        // --- Typed helpers (never throw; fall back to the provided default) ---

        public string AsString(string fallback = null) =>
            Type == NodeType.String ? StringValue : fallback;

        public float AsFloat(float fallback = 0f) =>
            Type == NodeType.Number ? (float)NumberValue
            : Type == NodeType.String && float.TryParse(StringValue, NumberStyles.Float, CultureInfo.InvariantCulture, out float f) ? f
            : fallback;

        public int AsInt(int fallback = 0) =>
            Type == NodeType.Number ? (int)Math.Round(NumberValue)
            : Type == NodeType.String && int.TryParse(StringValue, out int n) ? n
            : fallback;

        public bool AsBool(bool fallback = false) =>
            Type == NodeType.Bool ? BoolValue : fallback;

        public List<string> AsStringList()
        {
            var result = new List<string>();
            if (Type == NodeType.Array)
            {
                foreach (var item in ArrayValue)
                {
                    string s = item.AsString();
                    if (s != null) result.Add(s);
                }
            }
            else if (Type == NodeType.String)
            {
                result.Add(StringValue);
            }
            return result;
        }

        /// <summary>Reads a required string field, appending a message when missing.</summary>
        public string RequireString(string key, List<string> errors, string context)
        {
            var node = Get(key);
            string value = node.AsString();
            if (string.IsNullOrWhiteSpace(value))
            {
                errors?.Add($"{context}: missing required string field '{key}'.");
                return null;
            }
            return value;
        }
    }
}
