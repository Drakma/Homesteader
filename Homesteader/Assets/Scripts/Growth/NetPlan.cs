using Homesteader.UI;
using UnityEngine;

namespace Homesteader.Growth
{
    /// <summary>
    /// The internet subscription (docs/INTERNET.md). A dish brings nothing in without a plan, and a plan caps what it brings in: the bandwidth is the
    /// least of the plan and what the dish itself gives in this weather. A plan is paid a month (28 days) ahead: the first month when it is taken,
    /// then each renewal as the month runs out; changing plan credits the unused days of the old one against the new. When a renewal cannot be
    /// paid the plan is cancelled and the internet goes down. The plan and the days left are saved (GameSave.netPlan, netPlanDaysLeft).
    /// </summary>
    public static class NetPlan
    {
        public sealed class Plan
        {
            public string Id, Name;
            public float Mbps, Price;   // megabits a second it allows; dollars a month
        }

        public static readonly Plan[] Plans =
        {
            new Plan { Id = "basic", Name = "Basic", Mbps = 25f, Price = 40f },
            new Plan { Id = "standard", Name = "Standard", Mbps = 100f, Price = 75f },
            new Plan { Id = "fast", Name = "Fast", Mbps = 250f, Price = 120f },
            new Plan { Id = "max", Name = "Max", Mbps = 500f, Price = 180f },
        };

        public const int PeriodDays = TimeConstants.DaysPerMonth;

        public static string CurrentId { get; private set; } = "";
        public static int DaysLeft { get; private set; }
        private static int s_lastDay = -1;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        public static void Reset() { CurrentId = ""; DaysLeft = 0; s_lastDay = -1; }

        public static Plan Current
        {
            get { foreach (Plan p in Plans) if (p.Id == CurrentId) return p; return null; }
        }

        /// <summary>Megabits a second the plan allows (0 with no plan: the dish brings nothing in).</summary>
        public static float CapMbps { get { Plan p = Current; return p != null ? p.Mbps : 0f; } }

        /// <summary>What switching to a plan costs now: its month, less the unused days of the plan held.</summary>
        public static float CostToSwitch(Plan to)
        {
            Plan cur = Current;
            float credit = cur != null ? cur.Price * Mathf.Clamp(DaysLeft, 0, PeriodDays) / PeriodDays : 0f;
            return Mathf.Max(0f, to.Price - credit);
        }

        /// <summary>Takes (or changes to) a plan, paying its first month. False when the money is not there.</summary>
        public static bool Subscribe(string id)
        {
            Plan to = null;
            foreach (Plan p in Plans) if (p.Id == id) to = p;
            HudState hud = HudState.Active;
            if (to == null || hud == null || to.Id == CurrentId) return false;
            if (!hud.SpendMoney(CostToSwitch(to))) return false;
            CurrentId = to.Id;
            DaysLeft = PeriodDays;
            return true;
        }

        /// <summary>Cancels the plan: the internet goes down at once (the days already paid are not refunded).</summary>
        public static void Cancel() { CurrentId = ""; DaysLeft = 0; }

        public static void Restore(string id, int daysLeft)
        {
            CurrentId = id ?? "";
            if (Current == null) CurrentId = "";
            DaysLeft = CurrentId == "" ? 0 : Mathf.Clamp(daysLeft, 1, PeriodDays);
            s_lastDay = -1;
        }

        /// <summary>Counts the days down and renews the plan when the month runs out (called a few times a second; it acts once a game day).</summary>
        public static void Tick()
        {
            if (TimeSystem.Instance == null) return;
            int day = TimeSystem.Instance.DayOfYear;
            if (s_lastDay < 0) { s_lastDay = day; return; }
            if (day == s_lastDay) return;
            int passed = ((day - s_lastDay) % TimeConstants.DaysPerYear + TimeConstants.DaysPerYear) % TimeConstants.DaysPerYear;
            s_lastDay = day;
            Plan plan = Current;
            if (plan == null) return;
            DaysLeft -= Mathf.Max(1, passed);
            HudState hud = HudState.Active;
            while (DaysLeft <= 0 && plan != null)
            {
                if (hud != null && hud.SpendMoney(plan.Price))
                {
                    DaysLeft += PeriodDays;
                    ToastNotificationSystem.ShowInfo("Internet plan renewed", plan.Name + " plan: $" + plan.Price.ToString("0") + " for the next month.");
                }
                else
                {
                    ToastNotificationSystem.ShowWarning("Internet cut off", "The " + plan.Name + " plan could not be paid ($" + plan.Price.ToString("0") + "). Take a plan again in ResView.");
                    Cancel();
                    plan = null;
                }
            }
        }
    }
}
