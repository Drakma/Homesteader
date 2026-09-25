// GigsApp.cs - "Gigs" phone app: browse job offers, take one, work a shift for daily pay.
// Wired into PhoneController (tile, view, back button).

using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UIElements;

namespace Homesteader.UI
{
    public enum JobLocation { OnSite, Remote }

    public sealed class JobOffer
    {
        public string Id;
        public string Title;
        public string Employer;
        public float HourlyWage;   // USD, approximate US median
        public int HoursPerDay;    // 2, 4 or 8
        public JobLocation Location;
        public string Blurb;
        public float StartMinute = 8f * 60f;   // shift start, minutes after midnight (default 08:00)
        public bool IsOvernight => StartMinute >= 20f * 60f;
        public string StartLabel { get { int m = (int)StartMinute; int h = m / 60 % 24; return $"{(h % 12 == 0 ? 12 : h % 12)}:{m % 60:00} {(h < 12 ? "AM" : "PM")}"; } }
        public float DailyPay => HourlyWage * HoursPerDay;
    }

    public static class JobBoard
    {
        public static readonly List<JobOffer> Offers = new List<JobOffer>
        {
            new JobOffer { Id = "cashier",   Title = "Grocery Cashier",        Employer = "Valley Market",         HourlyWage = 14.50f, HoursPerDay = 8, Location = JobLocation.OnSite, Blurb = "Ring up customers and bag groceries." },
            new JobOffer { Id = "farmhand",  Title = "Farm Hand",              Employer = "Miller Family Farms",   HourlyWage = 15.75f, HoursPerDay = 8, Location = JobLocation.OnSite, Blurb = "Planting, harvesting and general chores." },
            new JobOffer { Id = "carpenter", Title = "Carpenter's Helper",     Employer = "Oak & Nail Builders",   HourlyWage = 22.00f, HoursPerDay = 8, Location = JobLocation.OnSite, Blurb = "Frame, haul lumber, and learn the trade." },
            new JobOffer { Id = "trucker",   Title = "Delivery Driver",        Employer = "County Freight Co.",    HourlyWage = 21.50f, HoursPerDay = 8, Location = JobLocation.OnSite, Blurb = "Local routes, home by supper." },
            new JobOffer { Id = "feedstore", Title = "Feed Store Clerk",       Employer = "Hay There Feed & Seed", HourlyWage = 15.00f, HoursPerDay = 4, Location = JobLocation.OnSite, Blurb = "Load feed and help customers half-days." },
            new JobOffer { Id = "diner",     Title = "Diner Server",           Employer = "Sunrise Diner",         HourlyWage = 12.00f, HoursPerDay = 4, Location = JobLocation.OnSite, Blurb = "Breakfast rush shift. Wage before tips." },
            new JobOffer { Id = "mechanic",  Title = "Auto Mechanic",          Employer = "Shift Happens Garage",  HourlyWage = 27.50f, HoursPerDay = 8, Location = JobLocation.OnSite, Blurb = "Diagnose and repair trucks and tractors." },
            new JobOffer { Id = "sitter",    Title = "After-School Sitter",    Employer = "Local Families",        HourlyWage = 16.00f, HoursPerDay = 2, Location = JobLocation.OnSite, Blurb = "Two hours of homework help and snacks." },
            new JobOffer { Id = "support",   Title = "Customer Support Rep",   Employer = "Nimbus Help Desk",      HourlyWage = 18.50f, HoursPerDay = 8, Location = JobLocation.Remote, Blurb = "Answer chats and calls from home." },
            new JobOffer { Id = "transcribe",Title = "Transcriptionist",       Employer = "ClearWord Services",    HourlyWage = 20.00f, HoursPerDay = 4, Location = JobLocation.Remote, Blurb = "Turn audio into text, on your schedule." },
            new JobOffer { Id = "bookkeeper",Title = "Freelance Bookkeeper",   Employer = "Ledger Lane LLC",       HourlyWage = 29.00f, HoursPerDay = 4, Location = JobLocation.Remote, Blurb = "Reconcile small-business books online." },
            new JobOffer { Id = "tutor",     Title = "Online Tutor",           Employer = "BrightPath Learning",   HourlyWage = 25.00f, HoursPerDay = 2, Location = JobLocation.Remote, Blurb = "Two one-hour video sessions a day." },
            new JobOffer { Id = "guard",     Title = "Night Security Guard",   Employer = "Ironwood Security",     HourlyWage = 17.50f, HoursPerDay = 8, Location = JobLocation.OnSite, StartMinute = 22f * 60f, Blurb = "Overnight patrol of the warehouse yard." },
            new JobOffer { Id = "stocker",   Title = "Overnight Stocker",      Employer = "Valley Market",         HourlyWage = 16.50f, HoursPerDay = 8, Location = JobLocation.OnSite, StartMinute = 22f * 60f, Blurb = "Restock shelves while the store is closed." },
            new JobOffer { Id = "nightchat", Title = "Night Support Agent",    Employer = "Nimbus Help Desk",      HourlyWage = 19.50f, HoursPerDay = 4, Location = JobLocation.Remote, StartMinute = 23f * 60f, Blurb = "Late-night chat queue, from home." },
        };

        public const float ShiftStartMinute = 8f * 60f;   // 08:00
        public const float WorkSpeed = 100f;               // sim speed while at work
        public const int MaxSkips = 3;

        public static JobOffer Current;
        public static int LastWorkedDay = -1;
        public static int StartDay = -1;
        public static int Skips;
        public static bool AtWork { get; private set; }
        public static bool DoneToday => TimeSystem.Instance != null && _startedDay == TimeSystem.Instance.DayOfYear;
        public static event System.Action Changed;
        private static int _startedDay = -1;

        private static int _promptedDay = -1;
        private static bool _prompting;
        private static float _shiftEndAbs;

        public static void TakeJob(JobOffer job, int today)
        {
            Current = job;
            StartDay = today;
            _startedDay = today;
            Skips = 0;
            EndShift(false);
        }

        public static void Quit()
        {
            Current = null;
            EndShift(false);
        }

        private static float NowAbs()
        {
            var ts = TimeSystem.Instance;
            return ts.DayOfYear * TimeConstants.CycleGameMinutes + ts.MinuteOfDay;
        }

        public static void GoToWork()
        {
            if (Current == null || AtWork) return;
            int today = TimeSystem.Instance.DayOfYear;
            if (_startedDay == today) return;   // one shift per day
            _startedDay = today;
            _prompting = false;
            AtWork = true;
            _shiftEndAbs = NowAbs() + Current.HoursPerDay * 60f;
            Changed?.Invoke();
        }

        private static void EndShift(bool paid)
        {
            AtWork = false;
            _prompting = false;
            if (paid && Current != null)
            {
                HudState.Active.AddMoney(Current.DailyPay);
                LastWorkedDay = TimeSystem.Instance.DayOfYear;
                Skips = 0;
            }
            Changed?.Invoke();
        }

        private static void Skip()
        {
            _prompting = false;
            if (Current == null) return;
            Skips++;
            _startedDay = TimeSystem.Instance.DayOfYear;   // a skipped shift uses up today
            if (Skips >= MaxSkips)
            {
                string title = Current.Title;
                string employer = Current.Employer;
                Current = null;
                Skips = 0;
                HudBindings.Instance?.ShowModal("You're Fired", $"Too many skipped shifts. {employer} let you go from your {title} job.");
            }
            Changed?.Invoke();
        }

        /// <summary>Call every frame: prompts at shift start, runs the shift, pays when it ends.</summary>
        public static void Tick()
        {
            var ts = TimeSystem.Instance;
            if (ts == null || Current == null) return;
            var hud = HudBindings.Instance;

            if (AtWork)
            {
                if (NowAbs() >= _shiftEndAbs) EndShift(true);
                return;
            }

            if (_prompting)
            {
                // Modal dismissed with the X or by clicking outside counts as a skip.
                if (hud != null && !hud.IsModalOpen) Skip();
                return;
            }

            int day = ts.DayOfYear;
            if (hud == null || day == _promptedDay || day == StartDay || ts.MinuteOfDay < Current.StartMinute) return;
            if (hud.IsModalOpen) return;

            _promptedDay = day;
            _prompting = true;
            hud.ShowModal("Time for Work",
                $"Your {Current.Title} shift at {Current.Employer} starts now ({Current.HoursPerDay}h, ${Current.DailyPay:F2}).\nSkipped shifts: {Skips}/{MaxSkips} - too many and you're fired.",
                onConfirm: GoToWork, onCancel: () => { Quit(); });
            if (!hud.IsModalOpen) _prompting = false;
        }
    }

    public sealed class GigsApp
    {
        private readonly VisualElement _list;
        private readonly VisualElement _currentCard;
        private readonly Label _currentTitle;
        private readonly Label _currentDetail;
        private readonly Button _workBtn;
        private readonly Button _quitBtn;
        private readonly Label _filterHint;
        private string _filter = "All";
        private readonly List<Button> _filterBtns = new List<Button>();

        public GigsApp(VisualElement root)
        {
            _list = root.Q<VisualElement>("GigsListContainer");
            _currentCard = root.Q<VisualElement>("GigsCurrentCard");
            _currentTitle = root.Q<Label>("GigsCurrentTitle");
            _currentDetail = root.Q<Label>("GigsCurrentDetail");
            _workBtn = root.Q<Button>("GigsWorkBtn");
            _quitBtn = root.Q<Button>("GigsQuitBtn");
            _filterHint = root.Q<Label>("GigsHint");

            foreach (string f in new[] { "All", "On-site", "Remote", "2h", "4h", "8h" })
            {
                Button b = root.Q<Button>("GigsFilter" + f.Replace("-", ""));
                if (b == null) continue;
                string filter = f;
                b.clicked += () => { _filter = filter; Refresh(); };
                _filterBtns.Add(b);
            }

            JobBoard.Changed += Refresh;
            if (_workBtn != null) _workBtn.clicked += () => { JobBoard.GoToWork(); Refresh(); };
            if (_quitBtn != null) _quitBtn.clicked += () => { JobBoard.Quit(); Refresh(); };
        }

        public void Refresh()
        {
            if (_list == null) return;

            foreach (Button b in _filterBtns)
            {
                string f = b.name.Substring("GigsFilter".Length);
                string label = f == "Onsite" ? "On-site" : f;
                b.EnableInClassList("admin-chip-btn--active", label == _filter);
            }

            JobOffer cur = JobBoard.Current;
            if (_currentCard != null) _currentCard.style.display = cur == null ? DisplayStyle.None : DisplayStyle.Flex;
            if (cur != null)
            {
                if (_currentTitle != null) _currentTitle.text = "CURRENT JOB: " + cur.Title;
                bool worked = JobBoard.DoneToday;
                if (_currentDetail != null)
                    _currentDetail.text = $"{cur.Employer} • {cur.HoursPerDay}h/day • ${cur.DailyPay:F2}/day • paid at end of shift" + (JobBoard.AtWork ? " • at work (100x)" : "") + $" • skips {JobBoard.Skips}/{JobBoard.MaxSkips}";
                if (_workBtn != null)
                {
                    _workBtn.SetEnabled(!worked && !JobBoard.AtWork);
                    _workBtn.text = JobBoard.AtWork ? "At Work..." : worked ? "Done for Today" : "Go to Work Now";
                }
            }

            _list.Clear();
            foreach (JobOffer job in JobBoard.Offers)
            {
                if (!Matches(job)) continue;
                _list.Add(BuildCard(job, cur == job));
            }
            if (_list.childCount == 0)
            {
                var none = new Label("No jobs match this filter.");
                none.AddToClassList("store-empty-search-label");
                _list.Add(none);
            }
        }

        private bool Matches(JobOffer j)
        {
            switch (_filter)
            {
                case "On-site": return j.Location == JobLocation.OnSite;
                case "Remote": return j.Location == JobLocation.Remote;
                case "2h": return j.HoursPerDay == 2;
                case "4h": return j.HoursPerDay == 4;
                case "8h": return j.HoursPerDay == 8;
                default: return true;
            }
        }

        private VisualElement BuildCard(JobOffer job, bool isCurrent)
        {
            var card = new VisualElement();
            card.AddToClassList("gig-card");

            var top = new VisualElement();
            top.AddToClassList("gig-card-top");
            var title = new Label(job.Title);
            title.AddToClassList("store-item-name");
            var pay = new Label($"${job.DailyPay:F0}/day");
            pay.AddToClassList("gig-pay");
            top.Add(title);
            top.Add(pay);
            card.Add(top);

            var employer = new Label(job.Employer);
            employer.AddToClassList("store-item-price");
            card.Add(employer);

            var chips = new VisualElement();
            chips.AddToClassList("gig-chip-row");
            chips.Add(Chip($"{job.HoursPerDay}h/day"));
            chips.Add(Chip(job.IsOvernight ? $"Overnight {job.StartLabel}" : $"Starts {job.StartLabel}"));
            chips.Add(Chip($"${job.HourlyWage:F2}/hr"));
            var loc = Chip(job.Location == JobLocation.Remote ? "Work from home" : "On-site");
            if (job.Location == JobLocation.Remote) loc.AddToClassList("gig-chip--remote");
            chips.Add(loc);
            card.Add(chips);

            var blurb = new Label(job.Blurb);
            blurb.AddToClassList("gig-blurb");
            card.Add(blurb);

            var btn = new Button();
            btn.AddToClassList("store-item-buy-btn");
            btn.text = isCurrent ? "Current Job" : "Take Job";
            btn.SetEnabled(!isCurrent);
            btn.clicked += () => { JobBoard.TakeJob(job, CurrentDay()); Refresh(); };
            card.Add(btn);
            return card;
        }

        private static VisualElement Chip(string text)
        {
            var l = new Label(text);
            l.AddToClassList("gig-chip");
            return l;
        }

        private static int CurrentDay()
        {
            return TimeSystem.Instance != null ? TimeSystem.Instance.DayOfYear : 0;
        }

    }
}
