// PhoneController.cs - Smartphone controller for the Homesteader In-Game OS.
//
// Toggled via Tab key. Features:
// - Physical device slide-in/out animation on right-middle of viewport
// - Status bar (real-time clock synchronized with TimeSystem, signal, battery)
// - Home launcher grid for 6 modular apps
// - Volt / Grid OS (solar wattage, battery percentage, load)
// - ResView (potable water, diesel/propane fuel, internet telemetry)
// - Store Engine for Homestead Depot, Pantry & Grocer, and Valley Feed & Seed
//   with live item cards, cart calculation, and delivery order workflow.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Homesteader.Modding;
using UnityEngine;
using UnityEngine.UIElements;

namespace Homesteader.UI
{
    public sealed class PhoneController
    {
        public enum AppView
        {
            Home,
            Volt,
            Res,
            StoreDepot,
            StoreGrocer,
            StoreFeed,
            Bank,
            Market,
            Almanac,
            Mods,
            Admin,
            Gigs,
        }

        public struct StoreItem
        {
            public string Id;
            public string Name;
            public string Category;
            public float Price;
            public string IconGlyph;
            public string Unit;
        }

        private VisualElement _root;
        private VisualElement _phoneWrapper;

        // Status bar
        private Label _phoneClock;
        private VisualElement _phoneCelestialIcon;
        private VisualElement _phoneBatteryFill;
        private Label _phoneWeatherTemp;
        private Label _phoneWeatherDesc;

        // Viewports
        private VisualElement _phoneHome;
        private VisualElement _phoneLauncherViewport;
        private VisualElement _phoneLauncherTrack;
        private VisualElement _phonePageDotsRow;
        private VisualElement _pageDot0;
        private VisualElement _pageDot1;
        private int _currentLauncherPage = 0;

        private VisualElement _viewVolt;
        private VisualElement _viewRes;
        private VisualElement _viewStore;
        private VisualElement _viewBank;
        private VisualElement _viewMarket;
        private VisualElement _viewAdmin;
        private VisualElement _viewMods;
        private VisualElement _viewGigs;

        // App Launcher Tiles
        private VisualElement _appTileVolt;
        private VisualElement _appTileRes;
        private VisualElement _appTileAlmanac;
        private VisualElement _appTileLumber;
        private VisualElement _appTileDepot;
        private VisualElement _appTileGrocer;
        private VisualElement _appTileFeed;
        private VisualElement _appTileBank;
        private VisualElement _appTileMarket;
        private VisualElement _appTileVehicles;
        private VisualElement _appTileWater;
        private VisualElement _appTileLivestock;
        private VisualElement _appTileEquipment;
        private VisualElement _appTileDealership;
        private VisualElement _appTileTrailerShack;
        private VisualElement _appTileVoltvision;
        private VisualElement _appTileFurniture;
        private VisualElement _appTileMods;
        private VisualElement _appTileAdmin;
        private VisualElement _appTileGigs;

        // Navigation
        private Button _voltBackBtn;
        private Button _resBackBtn;
        private Button _storeBackBtn;
        private Button _bankBackBtn;
        private Button _marketBackBtn;
        private Button _modsBackBtn;
        private Button _adminBackBtn;
        private Button _gigsBackBtn;
        private VisualElement _phoneHomeBtn;
        private GigsApp _gigsApp;

        // Admin App Elements
        private Button _adminAssetsBtn;
        private Button _adminAssetsCardBtn;
        private Button _adminSeasonWinterBtn;
        private Button _adminSeasonSpringBtn;
        private Button _adminSeasonSummerBtn;
        private Button _adminSeasonAutumnBtn;
        private Label _adminDayLabel;
        private Label _adminDaylightLabel;
        private Label _adminAstroLabel;
        private Button _adminJumpSpringEquinoxBtn;
        private Button _adminJumpSummerSolsticeBtn;
        private Button _adminJumpAutumnEquinoxBtn;
        private Button _adminJumpWinterSolsticeBtn;
        private Button _adminDaySub7;
        private Button _adminDaySub1;
        private Button _adminDayAdd1;
        private Button _adminDayAdd7;
        private SliderInt _adminDaySlider;
        private Button _adminTimeDawnBtn;
        private Button _adminTimeNoonBtn;
        private Button _adminTimeDuskBtn;
        private Button _adminTimeNightBtn;
        private Label _adminTimeLabel;
        private VisualElement _adminTimeIcon;
        private Slider _adminTimeSlider;
        private Button _adminVitalsResetBtn;
        private Button _adminVitalsMaxBtn;
        private Label _adminVitalWellnessLabel;
        private Button _adminVitalWellnessZeroBtn;
        private SliderInt _adminVitalWellnessSlider;
        private Label _adminVitalStaminaLabel;
        private Button _adminVitalStaminaZeroBtn;
        private SliderInt _adminVitalStaminaSlider;
        private Label _adminVitalThirstLabel;
        private Button _adminVitalThirstZeroBtn;
        private SliderInt _adminVitalThirstSlider;
        private Label _adminVitalHungerLabel;
        private Button _adminVitalHungerZeroBtn;
        private SliderInt _adminVitalHungerSlider;
        private Button _adminUnitMetricBtn;
        private Button _adminUnitImperialBtn;
        private Button _adminResResetDefaultsBtn;
        private Label _adminResWaterLabel;
        private TextField _adminResWaterInput;
        private Button _adminResWaterSetBtn;
        private Label _adminResElecLabel;
        private TextField _adminResElecInput;
        private Button _adminResElecSetBtn;
        private Label _adminResBandwidthLabel;
        private TextField _adminResBandwidthInput;
        private Button _adminResBandwidthSetBtn;
        private Label _adminResFuelLabel;
        private TextField _adminResFuelInput;
        private Button _adminResFuelSetBtn;
        private Label _adminResMoneyLabel;
        private TextField _adminResMoneyInput;
        private Button _adminResMoneySetBtn;
        private Button _adminAddMoney500;
        private Button _adminAddMoney5000;
        private Button _adminClearDebtBtn;

        // Admin Weather Elements
        private Button _adminWeatherAutoBtn;
        private Button _adminWeatherSunnyBtn;
        private Button _adminWeatherPartlyCloudyBtn;
        private Button _adminWeatherCloudyBtn;
        private Button _adminWeatherRainBtn;
        private Button _adminWeatherThunderstormBtn;
        private Button _adminWeatherSnowBtn;
        private Button _adminWeatherBlizzardBtn;
        private Button _adminWeatherWindBtn;
        private Button _adminWeatherFogBtn;

        private bool _isUpdatingAdminUI;

        // Almanac App Elements
        private VisualElement _viewAlmanac;
        private Button _almanacBackBtn;
        private Label _almanacTodayTitle;
        private Label _almanacTodayDetails;
        private Button _almanacTabDailyBtn;
        private Button _almanacTabWeeklyBtn;
        private VisualElement _almanacDailyContainer;
        private VisualElement _almanacWeeklyContainer;
        private int _lastAlmanacDayRendered = -1;
        private bool _isAlmanacWeeklyTab = false;
        private static readonly Dictionary<string, Texture2D> s_weatherTextures = new Dictionary<string, Texture2D>();

        // Mods App Elements
        private TextField _modsSearchInput;
        private VisualElement _modsCategoriesContainer;
        private VisualElement _modsListContainer;
        private VisualElement _modsCategoryNav;
        private Button _modsCategoryBackBtn;
        private Label _modsCategoryTitle;
        private Button _modsCategoryToggleBtn;
        private string _selectedModCategory = null; // null = categories overview, non-null = viewing specific category
        private string _activeModSearchQuery = "";

        public class ModItemEntry
        {
            public string Id;
            public string Name;
            public string Category;
            public string Description;
            public string Author;
            public string Version;
            public int AssetCount;
            public string FolderPath;
            public bool IsDisabled;
            public string CategoryFolderPath;
            public bool IsCategoryDisabled;
        }

        private static List<ModItemEntry> s_cachedModEntries;

        // Res App Elements
        private Label _resWaterText;
        private Label _resFuelText;

        // Volt App Elements
        private Label _gridSolarWatts;
        private VisualElement _gridSolarFill;
        private Label _gridBatteryPct;
        private VisualElement _gridBatteryFill;
        private Label _gridLoadWatts;

        // Store App Elements
        private Label _storeTitle;
        private VisualElement _storeBanner;
        private Label _storeBannerText;
        private TextField _storeSearchInput;
        private VisualElement _storeItemsContainer;
        private Label _storeCartCount;
        private Label _storeCartTotal;
        private Button _storeCheckoutBtn;
        private List<StoreItem> _currentStoreAllItems;
        private string _storeSearchQuery = "";

        // Bank App Elements
        private Label _bankBalanceText;
        private Label _bankLoanDebtText;
        private Label _bankDailyInterestText;
        private Button _bankPay100Btn;
        private Button _bankPay500Btn;
        private Button _bankPayAllBtn;
        private Button _bankTake500Btn;
        private Button _bankTake2500Btn;
        private Button _bankTake10000Btn;

        // Market App Elements
        private Button _marketTabBuyBtn;
        private Button _marketTabSellBtn;
        private ScrollView _marketBuyScroll;
        private ScrollView _marketSellScroll;
        private VisualElement _marketBuyContainer;
        private VisualElement _marketSellContainer;

        // State
        private bool _isOpen = false;
        private AppView _currentView = AppView.Home;
        private readonly Dictionary<string, int> _cart = new Dictionary<string, int>();
        private readonly Action<string, string, Action, Action> _showModalCallback;

        public bool IsOpen => _isOpen;

        public PhoneController(VisualElement root, Action<string, string, Action, Action> showModalCallback)
        {
            _root = root;
            _showModalCallback = showModalCallback;
            BindElements();
            WireEvents();
        }

        private void BindElements()
        {
            if (_root == null) return;

            _phoneWrapper = _root.Q<VisualElement>("PhoneWrapper");

            _phoneClock = _root.Q<Label>("PhoneClock");
            _phoneCelestialIcon = _root.Q<VisualElement>("PhoneCelestialIcon");
            _phoneBatteryFill = _root.Q<VisualElement>("PhoneBatteryFill");
            _phoneWeatherTemp = _root.Q<Label>("PhoneWeatherTemp");
            _phoneWeatherDesc = _root.Q<Label>("PhoneWeatherDesc");

            _phoneHome = _root.Q<VisualElement>("PhoneHome");
            _phoneLauncherViewport = _root.Q<VisualElement>("PhoneLauncherViewport");
            _phoneLauncherTrack = _root.Q<VisualElement>("PhoneLauncherTrack");
            _phonePageDotsRow = _root.Q<VisualElement>("PhonePageDotsRow");
            _pageDot0 = _root.Q<VisualElement>("PageDot0") ?? _root.Q<VisualElement>("PhoneDot0");
            _pageDot1 = _root.Q<VisualElement>("PageDot1") ?? _root.Q<VisualElement>("PhoneDot1");
            _viewVolt = _root.Q<VisualElement>("ViewVolt");
            _viewRes = _root.Q<VisualElement>("ViewRes");
            _viewStore = _root.Q<VisualElement>("ViewStore");
            _viewBank = _root.Q<VisualElement>("ViewBank");
            _viewMarket = _root.Q<VisualElement>("ViewMarket");
            _viewMods = _root.Q<VisualElement>("ViewMods");
            _viewGigs = _root.Q<VisualElement>("ViewGigs");

            _appTileVolt = _root.Q<VisualElement>("AppTileVolt");
            _appTileRes = _root.Q<VisualElement>("AppTileRes");
            _appTileAlmanac = _root.Q<VisualElement>("AppTileAlmanac");
            _appTileLumber = _root.Q<VisualElement>("AppTileLumber");
            _appTileDepot = _root.Q<VisualElement>("AppTileDepot");
            _appTileGrocer = _root.Q<VisualElement>("AppTileGrocer");
            _appTileFeed = _root.Q<VisualElement>("AppTileFeed");
            _appTileBank = _root.Q<VisualElement>("AppTileBank");
            _appTileMarket = _root.Q<VisualElement>("AppTileMarket");
            _appTileVehicles = _root.Q<VisualElement>("AppTileVehicles");
            _appTileWater = _root.Q<VisualElement>("AppTileWater");
            _appTileLivestock = _root.Q<VisualElement>("AppTileLivestock");
            _appTileEquipment = _root.Q<VisualElement>("AppTileEquipment");
            _appTileDealership = _root.Q<VisualElement>("AppTileDealership");
            _appTileTrailerShack = _root.Q<VisualElement>("AppTileTrailerShack");
            _appTileVoltvision = _root.Q<VisualElement>("AppTileVoltvision");
            _appTileFurniture = _root.Q<VisualElement>("AppTileFurniture");
            _appTileMods = _root.Q<VisualElement>("AppTileMods");
            _appTileGigs = _root.Q<VisualElement>("AppTileGigs");

            _voltBackBtn = _root.Q<Button>("VoltBackBtn");
            _resBackBtn = _root.Q<Button>("ResBackBtn");
            _storeBackBtn = _root.Q<Button>("StoreBackBtn");
            _bankBackBtn = _root.Q<Button>("BankBackBtn");
            _marketBackBtn = _root.Q<Button>("MarketBackBtn");
            _modsBackBtn = _root.Q<Button>("ModsBackBtn");
            _gigsBackBtn = _root.Q<Button>("GigsBackBtn");
            _phoneHomeBtn = _root.Q<VisualElement>("PhoneHomeBtn");

            _gridSolarWatts = _root.Q<Label>("GridSolarWatts");
            _gridSolarFill = _root.Q<VisualElement>("GridSolarFill");
            _gridBatteryPct = _root.Q<Label>("GridBatteryPct");
            _gridBatteryFill = _root.Q<VisualElement>("GridBatteryFill");
            _gridLoadWatts = _root.Q<Label>("GridLoadWatts");

            _storeTitle = _root.Q<Label>("StoreTitle");
            _storeBanner = _root.Q<VisualElement>("StoreBanner");
            _storeBannerText = _root.Q<Label>("StoreBannerText");
            _storeSearchInput = _root.Q<TextField>("StoreSearchInput");
            _storeItemsContainer = _root.Q<VisualElement>("StoreItemsContainer");
            _storeCartCount = _root.Q<Label>("StoreCartCount");
            _storeCartTotal = _root.Q<Label>("StoreCartTotal");
            _storeCheckoutBtn = _root.Q<Button>("StoreCheckoutBtn");

            // Bank App
            _bankBalanceText = _root.Q<Label>("BankBalanceText");
            _bankLoanDebtText = _root.Q<Label>("BankLoanDebtText");
            _bankDailyInterestText = _root.Q<Label>("BankDailyInterestText");
            _bankPay100Btn = _root.Q<Button>("BankPay100Btn");
            _bankPay500Btn = _root.Q<Button>("BankPay500Btn");
            _bankPayAllBtn = _root.Q<Button>("BankPayAllBtn");
            _bankTake500Btn = _root.Q<Button>("BankTake500Btn");
            _bankTake2500Btn = _root.Q<Button>("BankTake2500Btn");
            _bankTake10000Btn = _root.Q<Button>("BankTake10000Btn");

            // Market App
            _marketTabBuyBtn = _root.Q<Button>("MarketTabBuyBtn");
            _marketTabSellBtn = _root.Q<Button>("MarketTabSellBtn");
            _marketBuyScroll = _root.Q<ScrollView>("MarketBuyScroll");
            _marketSellScroll = _root.Q<ScrollView>("MarketSellScroll");
            _marketBuyContainer = _root.Q<VisualElement>("MarketBuyContainer");
            _marketSellContainer = _root.Q<VisualElement>("MarketSellContainer");

            // Admin App
            _viewAdmin = _root.Q<VisualElement>("ViewAdmin");
            _appTileAdmin = _root.Q<VisualElement>("AppTileAdmin");
            _adminBackBtn = _root.Q<Button>("AdminBackBtn");
            _adminAssetsBtn = _root.Q<Button>("AdminAssetsBtn");
            _adminAssetsCardBtn = _root.Q<Button>("AdminAssetsCardBtn");
            _adminSeasonWinterBtn = _root.Q<Button>("AdminSeasonWinterBtn");
            _adminSeasonSpringBtn = _root.Q<Button>("AdminSeasonSpringBtn");
            _adminSeasonSummerBtn = _root.Q<Button>("AdminSeasonSummerBtn");
            _adminSeasonAutumnBtn = _root.Q<Button>("AdminSeasonAutumnBtn");
            _adminDayLabel = _root.Q<Label>("AdminDayLabel");
            _adminDaySub7 = _root.Q<Button>("AdminDaySub7");
            _adminDaySub1 = _root.Q<Button>("AdminDaySub1");
            _adminDayAdd1 = _root.Q<Button>("AdminDayAdd1");
            _adminDayAdd7 = _root.Q<Button>("AdminDayAdd7");
            _adminDaySlider = _root.Q<SliderInt>("AdminDaySlider");
            _adminDaylightLabel = _root.Q<Label>("AdminDaylightLabel");
            _adminAstroLabel = _root.Q<Label>("AdminAstroLabel");
            _adminJumpSpringEquinoxBtn = _root.Q<Button>("AdminJumpSpringEquinoxBtn");
            _adminJumpSummerSolsticeBtn = _root.Q<Button>("AdminJumpSummerSolsticeBtn");
            _adminJumpAutumnEquinoxBtn = _root.Q<Button>("AdminJumpAutumnEquinoxBtn");
            _adminJumpWinterSolsticeBtn = _root.Q<Button>("AdminJumpWinterSolsticeBtn");
            _adminTimeDawnBtn = _root.Q<Button>("AdminTimeDawnBtn");
            _adminTimeNoonBtn = _root.Q<Button>("AdminTimeNoonBtn");
            _adminTimeDuskBtn = _root.Q<Button>("AdminTimeDuskBtn");
            _adminTimeNightBtn = _root.Q<Button>("AdminTimeNightBtn");
            _adminTimeLabel = _root.Q<Label>("AdminTimeLabel");
            _adminTimeIcon = _root.Q<VisualElement>("AdminTimeIcon");
            _adminTimeSlider = _root.Q<Slider>("AdminTimeSlider");
            _adminVitalsResetBtn = _root.Q<Button>("AdminVitalsResetBtn");
            _adminVitalsMaxBtn = _root.Q<Button>("AdminVitalsMaxBtn");
            _adminVitalWellnessLabel = _root.Q<Label>("AdminVitalWellnessLabel");
            _adminVitalWellnessZeroBtn = _root.Q<Button>("AdminVitalWellnessZeroBtn");
            _adminVitalWellnessSlider = _root.Q<SliderInt>("AdminVitalWellnessSlider");
            _adminVitalStaminaLabel = _root.Q<Label>("AdminVitalStaminaLabel");
            _adminVitalStaminaZeroBtn = _root.Q<Button>("AdminVitalStaminaZeroBtn");
            _adminVitalStaminaSlider = _root.Q<SliderInt>("AdminVitalStaminaSlider");
            _adminVitalThirstLabel = _root.Q<Label>("AdminVitalThirstLabel");
            _adminVitalThirstZeroBtn = _root.Q<Button>("AdminVitalThirstZeroBtn");
            _adminVitalThirstSlider = _root.Q<SliderInt>("AdminVitalThirstSlider");
            _adminVitalHungerLabel = _root.Q<Label>("AdminVitalHungerLabel");
            _adminVitalHungerZeroBtn = _root.Q<Button>("AdminVitalHungerZeroBtn");
            _adminVitalHungerSlider = _root.Q<SliderInt>("AdminVitalHungerSlider");
            _resWaterText = _root.Q<Label>("ResWaterText");
            _resFuelText = _root.Q<Label>("ResFuelText");

            _adminUnitMetricBtn = _root.Q<Button>("AdminUnitMetricBtn");
            _adminUnitImperialBtn = _root.Q<Button>("AdminUnitImperialBtn");
            _adminResResetDefaultsBtn = _root.Q<Button>("AdminResResetDefaultsBtn");
            _adminResWaterLabel = _root.Q<Label>("AdminResWaterLabel");
            _adminResWaterInput = _root.Q<TextField>("AdminResWaterInput");
            _adminResWaterSetBtn = _root.Q<Button>("AdminResWaterSetBtn");
            _adminResElecLabel = _root.Q<Label>("AdminResElecLabel");
            _adminResElecInput = _root.Q<TextField>("AdminResElecInput");
            _adminResElecSetBtn = _root.Q<Button>("AdminResElecSetBtn");
            _adminResBandwidthLabel = _root.Q<Label>("AdminResBandwidthLabel");
            _adminResBandwidthInput = _root.Q<TextField>("AdminResBandwidthInput");
            _adminResBandwidthSetBtn = _root.Q<Button>("AdminResBandwidthSetBtn");
            _adminResFuelLabel = _root.Q<Label>("AdminResFuelLabel");
            _adminResFuelInput = _root.Q<TextField>("AdminResFuelInput");
            _adminResFuelSetBtn = _root.Q<Button>("AdminResFuelSetBtn");
            _adminResMoneyLabel = _root.Q<Label>("AdminResMoneyLabel");
            _adminResMoneyInput = _root.Q<TextField>("AdminResMoneyInput");
            _adminResMoneySetBtn = _root.Q<Button>("AdminResMoneySetBtn");

            _adminAddMoney500 = _root.Q<Button>("AdminAddMoney500");
            _adminAddMoney5000 = _root.Q<Button>("AdminAddMoney5000");
            _adminClearDebtBtn = _root.Q<Button>("AdminClearDebtBtn");

            _adminWeatherAutoBtn = _root.Q<Button>("AdminWeatherAutoBtn");
            _adminWeatherSunnyBtn = _root.Q<Button>("AdminWeatherSunnyBtn");
            _adminWeatherPartlyCloudyBtn = _root.Q<Button>("AdminWeatherPartlyCloudyBtn");
            _adminWeatherCloudyBtn = _root.Q<Button>("AdminWeatherCloudyBtn");
            _adminWeatherRainBtn = _root.Q<Button>("AdminWeatherRainBtn");
            _adminWeatherThunderstormBtn = _root.Q<Button>("AdminWeatherThunderstormBtn");
            _adminWeatherSnowBtn = _root.Q<Button>("AdminWeatherSnowBtn");
            _adminWeatherBlizzardBtn = _root.Q<Button>("AdminWeatherBlizzardBtn");
            _adminWeatherWindBtn = _root.Q<Button>("AdminWeatherWindBtn");
            _adminWeatherFogBtn = _root.Q<Button>("AdminWeatherFogBtn");

            // Almanac App
            _viewAlmanac = _root.Q<VisualElement>("ViewAlmanac");
            _almanacBackBtn = _root.Q<Button>("AlmanacBackBtn");
            _almanacTodayTitle = _root.Q<Label>("AlmanacTodayTitle");
            _almanacTodayDetails = _root.Q<Label>("AlmanacTodayDetails");
            _almanacTabDailyBtn = _root.Q<Button>("AlmanacTabDailyBtn");
            _almanacTabWeeklyBtn = _root.Q<Button>("AlmanacTabWeeklyBtn");
            _almanacDailyContainer = _root.Q<VisualElement>("AlmanacDailyContainer");
            _almanacWeeklyContainer = _root.Q<VisualElement>("AlmanacWeeklyContainer");

            // Mods App
            _modsSearchInput = _root.Q<TextField>("ModsSearchInput");
            _modsCategoriesContainer = _root.Q<VisualElement>("ModsCategoriesContainer");
            _modsListContainer = _root.Q<VisualElement>("ModsListContainer");
            _modsCategoryNav = _root.Q<VisualElement>("ModsCategoryNav");
            _modsCategoryBackBtn = _root.Q<Button>("ModsCategoryBackBtn");
            _modsCategoryTitle = _root.Q<Label>("ModsCategoryTitle");
            _modsCategoryToggleBtn = _root.Q<Button>("ModsCategoryToggleBtn");
        }

        private void SuppressKeyboardNavigation(VisualElement element)
        {
            if (element == null) return;

            // Block spatial/directional UI navigation (WASD, Arrow keys) from scrolling or shifting focus while walking
            element.RegisterCallback<NavigationMoveEvent>(evt =>
            {
                evt.PreventDefault(); // StopPropagation alone still lets the default focus move happen
                evt.StopPropagation();
            }, TrickleDown.TrickleDown);

            // Block keyboard walking keys (WASD, Arrows) from scrolling UI Toolkit ScrollViews
            element.RegisterCallback<KeyDownEvent>(evt =>
            {
                // Allow text fields inside phone to accept normal text typing
                if (evt.target is TextField || (evt.target is VisualElement ve && ve.GetFirstAncestorOfType<TextField>() != null))
                {
                    return;
                }

                if (evt.keyCode == KeyCode.W || evt.keyCode == KeyCode.S ||
                    evt.keyCode == KeyCode.A || evt.keyCode == KeyCode.D ||
                    evt.keyCode == KeyCode.UpArrow || evt.keyCode == KeyCode.DownArrow ||
                    evt.keyCode == KeyCode.LeftArrow || evt.keyCode == KeyCode.RightArrow)
                {
                    evt.PreventDefault();
                    evt.StopPropagation();
                }
            }, TrickleDown.TrickleDown);

            // Prevent ScrollViews and their scrollers from grabbing keyboard focus
            var scrollViews = element.Query<ScrollView>().ToList();
            foreach (var sv in scrollViews)
            {
                sv.focusable = false;
                if (sv.verticalScroller != null)
                {
                    sv.verticalScroller.focusable = false;
                    if (sv.verticalScroller.slider != null) sv.verticalScroller.slider.focusable = false;
                }
                if (sv.horizontalScroller != null)
                {
                    sv.horizontalScroller.focusable = false;
                    if (sv.horizontalScroller.slider != null) sv.horizontalScroller.slider.focusable = false;
                }
            }
        }

        private void WireEvents()
        {
            // Prevent WASD / Arrow directional navigation from scrolling phone scroll views while walking
            SuppressKeyboardNavigation(_phoneWrapper);

            // App Tiles Launch
            _appTileVolt?.RegisterCallback<ClickEvent>(evt => OpenApp(AppView.Volt));
            _appTileRes?.RegisterCallback<ClickEvent>(evt => OpenApp(AppView.Res));
            _appTileAlmanac?.RegisterCallback<ClickEvent>(evt => OpenApp(AppView.Almanac));
            _appTileLumber?.RegisterCallback<ClickEvent>(evt => OpenStore("Board Meeting", "store-banner-depot", "Milled Timber, Studs & Architectural Lumber", GetLumberItems()));
            _appTileDepot?.RegisterCallback<ClickEvent>(evt => OpenStore("Nail It", "store-banner-depot", "Hardware, Tools, Construction & Electrical", GetDepotItems()));
            _appTileGrocer?.RegisterCallback<ClickEvent>(evt => OpenStore("Lettuce Shop", "store-banner-grocer", "Fresh Valley Foods & Pantry Seed Supplies", GetGrocerItems()));
            _appTileFeed?.RegisterCallback<ClickEvent>(evt => OpenStore("Hay There", "store-banner-feed", "Livestock Feed, Straw, Bales & Minerals", GetFeedItems()));
            _appTileBank?.RegisterCallback<ClickEvent>(evt => OpenApp(AppView.Bank));
            _appTileMarket?.RegisterCallback<ClickEvent>(evt => OpenApp(AppView.Market));
            _appTileVehicles?.RegisterCallback<ClickEvent>(evt => OpenStore("Shift Happens", "store-banner-depot", "Vehicle Utility, Transmissions & Mechanical Parts", GetVehicleItems()));
            _appTileWater?.RegisterCallback<ClickEvent>(evt => OpenStore("Tank You", "store-banner-depot", "Rain Cisterns, Jet Well Pumps & Plumbing Supply", GetWaterItems()));
            _appTileLivestock?.RegisterCallback<ClickEvent>(evt => OpenStore("Drafting Behind You", "store-banner-feed", "Working Animals, Draft Harnesses & Livestock Care", GetLivestockItems()));
            _appTileEquipment?.RegisterCallback<ClickEvent>(evt => OpenStore("Tractor Beam", "store-banner-depot", "Heavy Tractors, Skidsteers & Implements", GetEquipmentItems()));
            _appTileDealership?.RegisterCallback<ClickEvent>(evt => OpenStore("Wheel Deal", "store-banner-depot", "Utility Vehicles, ATVs & Cargo Flatbeds", GetDealershipItems()));
            _appTileTrailerShack?.RegisterCallback<ClickEvent>(evt => OpenStore("Trailer Shack", "store-banner-trailershack", "Heavy-Duty Utility Trailers, Haulers & Secure Parts", GetTrailerShackItems()));
            _appTileVoltvision?.RegisterCallback<ClickEvent>(evt => OpenStore("Voltvision", "store-banner-voltvision", "Homestead Off-Grid Solar, Batteries & High-Tech Electronics", GetVoltvisionItems()));
            _appTileFurniture?.RegisterCallback<ClickEvent>(evt => OpenStore("Sofa So Good", "store-banner-grocer", "Artisan Homestead Furniture, Storage & Decor", GetFurnitureItems()));
            _appTileMods?.RegisterCallback<ClickEvent>(evt => OpenApp(AppView.Mods));
            _appTileGigs?.RegisterCallback<ClickEvent>(evt => OpenApp(AppView.Gigs));

            _pageDot0?.RegisterCallback<ClickEvent>(evt => GoToLauncherPage(0));
            _pageDot1?.RegisterCallback<ClickEvent>(evt => GoToLauncherPage(1));

            // Back & Home Navigation
            _voltBackBtn?.RegisterCallback<ClickEvent>(evt => ReturnHome());
            _resBackBtn?.RegisterCallback<ClickEvent>(evt => ReturnHome());
            _storeBackBtn?.RegisterCallback<ClickEvent>(evt => ReturnHome());
            _bankBackBtn?.RegisterCallback<ClickEvent>(evt => ReturnHome());
            _marketBackBtn?.RegisterCallback<ClickEvent>(evt => ReturnHome());
            _almanacBackBtn?.RegisterCallback<ClickEvent>(evt => ReturnHome());
            _modsBackBtn?.RegisterCallback<ClickEvent>(evt => HandleModsBack());
            _gigsBackBtn?.RegisterCallback<ClickEvent>(evt => ReturnHome());
            _modsCategoryBackBtn?.RegisterCallback<ClickEvent>(evt => GoToModCategories());
            _modsCategoryToggleBtn?.RegisterCallback<ClickEvent>(evt => ToggleCurrentCategory());
            _phoneHomeBtn?.RegisterCallback<ClickEvent>(evt => ReturnHome());

            // Almanac Tabs
            _almanacTabDailyBtn?.RegisterCallback<ClickEvent>(evt => SwitchAlmanacTab(false));
            _almanacTabWeeklyBtn?.RegisterCallback<ClickEvent>(evt => SwitchAlmanacTab(true));

            // Store Checkout & Search
            if (_storeCheckoutBtn != null)
            {
                _storeCheckoutBtn.clicked += HandleCheckout;
            }

            _storeSearchInput?.RegisterValueChangedCallback(evt =>
            {
                _storeSearchQuery = evt.newValue ?? "";
                FilterAndDisplayStoreItems();
            });

            // Bank Actions
            _bankPay100Btn?.RegisterCallback<ClickEvent>(evt => RepayLoan(100f));
            _bankPay500Btn?.RegisterCallback<ClickEvent>(evt => RepayLoan(500f));
            _bankPayAllBtn?.RegisterCallback<ClickEvent>(evt => RepayLoan(HudState.Active.LoanDebt));
            _bankTake500Btn?.RegisterCallback<ClickEvent>(evt => BorrowLoan(500f));
            _bankTake2500Btn?.RegisterCallback<ClickEvent>(evt => BorrowLoan(2500f));
            _bankTake10000Btn?.RegisterCallback<ClickEvent>(evt => BorrowLoan(10000f));

            // Market Tabs
            _marketTabBuyBtn?.RegisterCallback<ClickEvent>(evt => SwitchMarketTab(true));
            _marketTabSellBtn?.RegisterCallback<ClickEvent>(evt => SwitchMarketTab(false));

            // Admin App
            _appTileAdmin?.RegisterCallback<ClickEvent>(evt => OpenApp(AppView.Admin));
            _adminBackBtn?.RegisterCallback<ClickEvent>(evt => ReturnHome());
            _adminAssetsBtn?.RegisterCallback<ClickEvent>(evt => HudBindings.Instance?.OpenAssetSpawner());
            _adminAssetsCardBtn?.RegisterCallback<ClickEvent>(evt => HudBindings.Instance?.OpenAssetSpawner());

            // Seasons
            _adminSeasonWinterBtn?.RegisterCallback<ClickEvent>(evt => { TimeSystem.Instance.SetSeason(HomesteaderSeason.Winter); UpdateAdminDisplay(); });
            _adminSeasonSpringBtn?.RegisterCallback<ClickEvent>(evt => { TimeSystem.Instance.SetSeason(HomesteaderSeason.Spring); UpdateAdminDisplay(); });
            _adminSeasonSummerBtn?.RegisterCallback<ClickEvent>(evt => { TimeSystem.Instance.SetSeason(HomesteaderSeason.Summer); UpdateAdminDisplay(); });
            _adminSeasonAutumnBtn?.RegisterCallback<ClickEvent>(evt => { TimeSystem.Instance.SetSeason(HomesteaderSeason.Autumn); UpdateAdminDisplay(); });

            // Day steppers & slider
            _adminDaySub7?.RegisterCallback<ClickEvent>(evt => { TimeSystem.Instance.SetDayOfYear(TimeSystem.Instance.DayOfYear - 7); UpdateAdminDisplay(); });
            _adminDaySub1?.RegisterCallback<ClickEvent>(evt => { TimeSystem.Instance.SetDayOfYear(TimeSystem.Instance.DayOfYear - 1); UpdateAdminDisplay(); });
            _adminDayAdd1?.RegisterCallback<ClickEvent>(evt => { TimeSystem.Instance.SetDayOfYear(TimeSystem.Instance.DayOfYear + 1); UpdateAdminDisplay(); });
            _adminDayAdd7?.RegisterCallback<ClickEvent>(evt => { TimeSystem.Instance.SetDayOfYear(TimeSystem.Instance.DayOfYear + 7); UpdateAdminDisplay(); });
            _adminDaySlider?.RegisterValueChangedCallback(evt =>
            {
                if (!_isUpdatingAdminUI)
                {
                    TimeSystem.Instance.SetDayOfYear(evt.newValue);
                    UpdateAdminDayLabel();
                }
            });

            // Solstices & Equinoxes Jump buttons
            _adminJumpSpringEquinoxBtn?.RegisterCallback<ClickEvent>(evt => { TimeSystem.Instance.SetDayOfYear(TimeConstants.SpringEquinoxDay); UpdateAdminDisplay(); });
            _adminJumpSummerSolsticeBtn?.RegisterCallback<ClickEvent>(evt => { TimeSystem.Instance.SetDayOfYear(TimeConstants.SummerSolsticeDay); UpdateAdminDisplay(); });
            _adminJumpAutumnEquinoxBtn?.RegisterCallback<ClickEvent>(evt => { TimeSystem.Instance.SetDayOfYear(TimeConstants.AutumnalEquinoxDay); UpdateAdminDisplay(); });
            _adminJumpWinterSolsticeBtn?.RegisterCallback<ClickEvent>(evt => { TimeSystem.Instance.SetDayOfYear(TimeConstants.WinterSolsticeDay); UpdateAdminDisplay(); });

            // Time presets & slider
            _adminTimeDawnBtn?.RegisterCallback<ClickEvent>(evt => { TimeSystem.Instance.SetTimePreset(6f); UpdateAdminDisplay(); });
            _adminTimeNoonBtn?.RegisterCallback<ClickEvent>(evt => { TimeSystem.Instance.SetTimePreset(12f); UpdateAdminDisplay(); });
            _adminTimeDuskBtn?.RegisterCallback<ClickEvent>(evt => { TimeSystem.Instance.SetTimePreset(18f); UpdateAdminDisplay(); });
            _adminTimeNightBtn?.RegisterCallback<ClickEvent>(evt => { TimeSystem.Instance.SetTimePreset(0f); UpdateAdminDisplay(); });
            _adminTimeSlider?.RegisterValueChangedCallback(evt =>
            {
                if (!_isUpdatingAdminUI)
                {
                    TimeSystem.Instance.SetMinuteOfDay(evt.newValue);
                    UpdateAdminTimeLabel();
                }
            });

            // Vitals
            _adminVitalsResetBtn?.RegisterCallback<ClickEvent>(evt =>
            {
                HudState.Active.ResetVitalsToNeutral();
                UpdateAdminVitalsDisplay();
            });
            _adminVitalsMaxBtn?.RegisterCallback<ClickEvent>(evt =>
            {
                HudState.Active.MaxAllVitals();
                UpdateAdminVitalsDisplay();
            });
            _adminVitalWellnessZeroBtn?.RegisterCallback<ClickEvent>(evt =>
            {
                HudState.Active.SetVitalValue(VitalId.Wellness, 0);
                UpdateAdminVitalsDisplay();
            });
            _adminVitalWellnessSlider?.RegisterValueChangedCallback(evt =>
            {
                if (!_isUpdatingAdminUI)
                {
                    HudState.Active.SetVitalValue(VitalId.Wellness, evt.newValue);
                    UpdateVitalLabel(_adminVitalWellnessLabel, "Wellness", evt.newValue);
                }
            });

            _adminVitalStaminaZeroBtn?.RegisterCallback<ClickEvent>(evt =>
            {
                HudState.Active.SetVitalValue(VitalId.Stamina, 0);
                UpdateAdminVitalsDisplay();
            });
            _adminVitalStaminaSlider?.RegisterValueChangedCallback(evt =>
            {
                if (!_isUpdatingAdminUI)
                {
                    HudState.Active.SetVitalValue(VitalId.Stamina, evt.newValue);
                    UpdateVitalLabel(_adminVitalStaminaLabel, "Stamina", evt.newValue);
                }
            });

            _adminVitalThirstZeroBtn?.RegisterCallback<ClickEvent>(evt =>
            {
                HudState.Active.SetVitalValue(VitalId.Thirst, 0);
                UpdateAdminVitalsDisplay();
            });
            _adminVitalThirstSlider?.RegisterValueChangedCallback(evt =>
            {
                if (!_isUpdatingAdminUI)
                {
                    HudState.Active.SetVitalValue(VitalId.Thirst, evt.newValue);
                    UpdateVitalLabel(_adminVitalThirstLabel, "Thirst", evt.newValue);
                }
            });

            _adminVitalHungerZeroBtn?.RegisterCallback<ClickEvent>(evt =>
            {
                HudState.Active.SetVitalValue(VitalId.Hunger, 0);
                UpdateAdminVitalsDisplay();
            });
            _adminVitalHungerSlider?.RegisterValueChangedCallback(evt =>
            {
                if (!_isUpdatingAdminUI)
                {
                    HudState.Active.SetVitalValue(VitalId.Hunger, evt.newValue);
                    UpdateVitalLabel(_adminVitalHungerLabel, "Hunger", evt.newValue);
                }
            });

            // Measurement System
            _adminUnitMetricBtn?.RegisterCallback<ClickEvent>(evt =>
            {
                HudState.Active.Units = UnitSystem.Metric;
                UpdateAdminUnitButtons();
                UpdateAdminResourcesDisplay();
            });
            _adminUnitImperialBtn?.RegisterCallback<ClickEvent>(evt =>
            {
                HudState.Active.Units = UnitSystem.Imperial;
                UpdateAdminUnitButtons();
                UpdateAdminResourcesDisplay();
            });

            // Resources (typed value)
            _adminResResetDefaultsBtn?.RegisterCallback<ClickEvent>(evt =>
            {
                HudState.Active.ResetResourcesToDefault();
                UpdateAdminResourcesDisplay();
            });

            // Water
            _adminResWaterInput?.RegisterValueChangedCallback(evt =>
            {
                if (!_isUpdatingAdminUI && float.TryParse(evt.newValue, out float val) && val >= 0f)
                {
                    HudState.Active.SetWaterFromDisplay(val);
                }
            });
            _adminResWaterSetBtn?.RegisterCallback<ClickEvent>(evt =>
            {
                if (float.TryParse(_adminResWaterInput?.value, out float val))
                {
                    HudState.Active.SetWaterFromDisplay(Mathf.Max(0f, val));
                    UpdateAdminResourcesDisplay();
                }
            });

            // Electricity
            _adminResElecInput?.RegisterValueChangedCallback(evt =>
            {
                if (!_isUpdatingAdminUI && float.TryParse(evt.newValue, out float val) && val >= 0f)
                {
                    HudState.Active.SetElectricityFromDisplay(val);
                }
            });
            _adminResElecSetBtn?.RegisterCallback<ClickEvent>(evt =>
            {
                if (float.TryParse(_adminResElecInput?.value, out float val))
                {
                    HudState.Active.SetElectricityFromDisplay(Mathf.Max(0f, val));
                    UpdateAdminResourcesDisplay();
                }
            });

            // Bandwidth
            _adminResBandwidthInput?.RegisterValueChangedCallback(evt =>
            {
                if (!_isUpdatingAdminUI && float.TryParse(evt.newValue, out float val) && val >= 0f)
                {
                    HudState.Active.SetResourceAmount(ResourceId.Bandwidth, val);
                }
            });
            _adminResBandwidthSetBtn?.RegisterCallback<ClickEvent>(evt =>
            {
                if (float.TryParse(_adminResBandwidthInput?.value, out float val))
                {
                    HudState.Active.SetResourceAmount(ResourceId.Bandwidth, Mathf.Max(0f, val));
                    UpdateAdminResourcesDisplay();
                }
            });

            // Fuel
            _adminResFuelInput?.RegisterValueChangedCallback(evt =>
            {
                if (!_isUpdatingAdminUI && float.TryParse(evt.newValue, out float val) && val >= 0f)
                {
                    HudState.Active.SetFuelFromDisplay(val);
                }
            });
            _adminResFuelSetBtn?.RegisterCallback<ClickEvent>(evt =>
            {
                if (float.TryParse(_adminResFuelInput?.value, out float val))
                {
                    HudState.Active.SetFuelFromDisplay(Mathf.Max(0f, val));
                    UpdateAdminResourcesDisplay();
                }
            });

            // Money
            _adminResMoneyInput?.RegisterValueChangedCallback(evt =>
            {
                if (!_isUpdatingAdminUI && float.TryParse(evt.newValue, out float val) && val >= 0f)
                {
                    HudState.Active.Money = val;
                }
            });
            _adminResMoneySetBtn?.RegisterCallback<ClickEvent>(evt =>
            {
                if (float.TryParse(_adminResMoneyInput?.value, out float val))
                {
                    HudState.Active.Money = Mathf.Max(0f, val);
                    UpdateAdminResourcesDisplay();
                }
            });

            _adminAddMoney500?.RegisterCallback<ClickEvent>(evt =>
            {
                HudState.Active.AddMoney(500f);
                UpdateAdminResourcesDisplay();
            });
            _adminAddMoney5000?.RegisterCallback<ClickEvent>(evt =>
            {
                HudState.Active.AddMoney(5000f);
                UpdateAdminResourcesDisplay();
            });
            _adminClearDebtBtn?.RegisterCallback<ClickEvent>(evt =>
            {
                HudState.Active.ClearDebt();
                UpdateAdminResourcesDisplay();
            });

            // Weather
            _adminWeatherAutoBtn?.RegisterCallback<ClickEvent>(evt => { TimeSystem.Instance.ResetWeatherToAuto(); UpdateAdminDisplay(); });
            _adminWeatherSunnyBtn?.RegisterCallback<ClickEvent>(evt => { TimeSystem.Instance.SetWeather(HomesteaderWeather.Sunny); UpdateAdminDisplay(); });
            _adminWeatherPartlyCloudyBtn?.RegisterCallback<ClickEvent>(evt => { TimeSystem.Instance.SetWeather(HomesteaderWeather.PartlyCloudy); UpdateAdminDisplay(); });
            _adminWeatherCloudyBtn?.RegisterCallback<ClickEvent>(evt => { TimeSystem.Instance.SetWeather(HomesteaderWeather.Cloudy); UpdateAdminDisplay(); });
            _adminWeatherRainBtn?.RegisterCallback<ClickEvent>(evt => { TimeSystem.Instance.SetWeather(HomesteaderWeather.Rain); UpdateAdminDisplay(); });
            _adminWeatherThunderstormBtn?.RegisterCallback<ClickEvent>(evt => { TimeSystem.Instance.SetWeather(HomesteaderWeather.Thunderstorm); UpdateAdminDisplay(); });
            _adminWeatherSnowBtn?.RegisterCallback<ClickEvent>(evt => { TimeSystem.Instance.SetWeather(HomesteaderWeather.Snow); UpdateAdminDisplay(); });
            _adminWeatherBlizzardBtn?.RegisterCallback<ClickEvent>(evt => { TimeSystem.Instance.SetWeather(HomesteaderWeather.Blizzard); UpdateAdminDisplay(); });
            _adminWeatherWindBtn?.RegisterCallback<ClickEvent>(evt => { TimeSystem.Instance.SetWeather(HomesteaderWeather.Wind); UpdateAdminDisplay(); });
            _adminWeatherFogBtn?.RegisterCallback<ClickEvent>(evt => { TimeSystem.Instance.SetWeather(HomesteaderWeather.Fog); UpdateAdminDisplay(); });
        }

        public void GoToLauncherPage(int page)
        {
            _currentLauncherPage = Mathf.Clamp(page, 0, 1);
            if (_phoneLauncherTrack != null)
            {
                // Each page is 384px wide (matching 3 columns of 128px)
                float pageWidth = 384f;
                if (_phoneLauncherViewport != null && _phoneLauncherViewport.resolvedStyle.width > 0f)
                {
                    pageWidth = _phoneLauncherViewport.resolvedStyle.width;
                }
                float offset = -_currentLauncherPage * pageWidth;
                _phoneLauncherTrack.style.translate = new Translate(offset, 0f, 0f);
            }

            const string activeDotClass = "phone-page-dot--active";
            if (_pageDot0 != null)
            {
                if (_currentLauncherPage == 0) _pageDot0.AddToClassList(activeDotClass);
                else _pageDot0.RemoveFromClassList(activeDotClass);
            }
            if (_pageDot1 != null)
            {
                if (_currentLauncherPage == 1) _pageDot1.AddToClassList(activeDotClass);
                else _pageDot1.RemoveFromClassList(activeDotClass);
            }
        }

        public void Toggle()
        {
            if (_isOpen) Close();
            else Open();
        }

        public void Open()
        {
            _isOpen = true;
            if (_phoneWrapper != null)
            {
                _phoneWrapper.RemoveFromClassList("phone-wrapper--hidden");
            }
            UpdatePhoneStatus();
        }

        public void Close()
        {
            _isOpen = false;
            if (_phoneWrapper != null)
            {
                _phoneWrapper.AddToClassList("phone-wrapper--hidden");
            }
        }

        public void ReturnHome()
        {
            _currentView = AppView.Home;
            HideAllViews();
            if (_phoneHome != null) _phoneHome.RemoveFromClassList("phone-home--hidden");
            if (_phonePageDotsRow != null) _phonePageDotsRow.RemoveFromClassList("phone-page-dots-row--hidden");
        }

        public void OpenApp(AppView app)
        {
            _currentView = app;
            HideAllViews();

            switch (app)
            {
                case AppView.Volt:
                    if (_viewVolt != null) _viewVolt.RemoveFromClassList("phone-app-view--hidden");
                    UpdateVoltData();
                    break;
                case AppView.Res:
                    if (_viewRes != null) _viewRes.RemoveFromClassList("phone-app-view--hidden");
                    UpdateResAppData();
                    break;
                case AppView.StoreDepot:
                    OpenStore("Homestead Depot", "store-banner-depot", "Same-Day Flatbed Delivery • Direct to Pallet", GetDepotItems());
                    break;
                case AppView.StoreGrocer:
                    OpenStore("Pantry & Grocer", "store-banner-grocer", "Fresh Valley Foods & Pantry Seed Supplies", GetGrocerItems());
                    break;
                case AppView.StoreFeed:
                    OpenStore("Valley Feed & Seed", "store-banner-feed", "Livestock Feed, Straw, Bales & Minerals", GetFeedItems());
                    break;
                case AppView.Bank:
                    if (_viewBank != null) _viewBank.RemoveFromClassList("phone-app-view--hidden");
                    UpdateBankDisplay();
                    break;
                case AppView.Market:
                    if (_viewMarket != null) _viewMarket.RemoveFromClassList("phone-app-view--hidden");
                    OpenMarket();
                    break;
                case AppView.Almanac:
                    if (_viewAlmanac != null) _viewAlmanac.RemoveFromClassList("phone-app-view--hidden");
                    OpenAlmanac();
                    break;
                case AppView.Mods:
                    if (_viewMods != null) _viewMods.RemoveFromClassList("phone-app-view--hidden");
                    OpenMods();
                    break;
                case AppView.Admin:
                    if (_viewAdmin != null) _viewAdmin.RemoveFromClassList("phone-app-view--hidden");
                    UpdateAdminDisplay();
                    break;
                case AppView.Gigs:
                    if (_viewGigs != null) _viewGigs.RemoveFromClassList("phone-app-view--hidden");
                    if (_gigsApp == null) _gigsApp = new GigsApp(_root);
                    _gigsApp.Refresh();
                    break;
                default:
                    ReturnHome();
                    break;
            }
        }

        private void HideAllViews()
        {
            if (_phoneHome != null) _phoneHome.AddToClassList("phone-home--hidden");
            if (_phonePageDotsRow != null) _phonePageDotsRow.AddToClassList("phone-page-dots-row--hidden");
            if (_viewVolt != null) _viewVolt.AddToClassList("phone-app-view--hidden");
            if (_viewRes != null) _viewRes.AddToClassList("phone-app-view--hidden");
            if (_viewStore != null) _viewStore.AddToClassList("phone-app-view--hidden");
            if (_viewBank != null) _viewBank.AddToClassList("phone-app-view--hidden");
            if (_viewMarket != null) _viewMarket.AddToClassList("phone-app-view--hidden");
            if (_viewAlmanac != null) _viewAlmanac.AddToClassList("phone-app-view--hidden");
            if (_viewMods != null) _viewMods.AddToClassList("phone-app-view--hidden");
            if (_viewAdmin != null) _viewAdmin.AddToClassList("phone-app-view--hidden");
            if (_viewGigs != null) _viewGigs.AddToClassList("phone-app-view--hidden");
        }

        public void Tick()
        {
            if (!_isOpen) return;

            UpdatePhoneStatus();
            if (_currentView == AppView.Volt)
            {
                UpdateVoltData();
            }
            else if (_currentView == AppView.Res)
            {
                UpdateResAppData();
            }
            else if (_currentView == AppView.Almanac)
            {
                if (TimeSystem.Instance.DayOfYear != _lastAlmanacDayRendered)
                {
                    UpdateAlmanacDisplay();
                }
            }
            else if (_currentView == AppView.Admin && !_isUpdatingAdminUI)
            {
                UpdateAdminTimeLabel();
            }
        }

        private void UpdatePhoneStatus()
        {
            if (_phoneClock != null)
            {
                _phoneClock.text = TimeSystem.Instance.GetWallClock();
            }

            var snap = TimeSystem.Instance.Snapshot();
            if (_phoneCelestialIcon != null)
            {
                var tex = Resources.Load<Texture2D>("HUDTree/KitSprites/celestial/" + snap.CelestialIconId);
                if (tex != null)
                {
                    _phoneCelestialIcon.style.backgroundImage = new StyleBackground(tex);
                    _phoneCelestialIcon.style.display = DisplayStyle.Flex;
                }
            }

            if (_phoneWeatherDesc != null)
            {
                var units = HudState.Active.Units;
                string tempNow = TimeSystem.FormatTemperature(snap.TemperatureC, units);
                string hiLo = TimeSystem.FormatHighLow(snap.TodayHighC, snap.TodayLowC, units);
                _phoneWeatherDesc.text = $"{snap.Season} • {snap.MonthName} {snap.DayOfMonth} • {TimeSystem.GetWeatherName(snap.Weather)}";
                if (_phoneWeatherTemp != null)
                    _phoneWeatherTemp.text = $"{tempNow}  {hiLo}";
            }
        }

        private void UpdateVoltData()
        {
            // Calculate dynamic daylight factor from TimeSystem (0.0 at dawn/dusk/night to 1.0 at noon)
            float sunFactor = TimeSystem.Instance.GetDaylightFactor();
            float solarKw = Mathf.Max(0f, sunFactor * 3.6f);
            if (_gridSolarWatts != null)
            {
                _gridSolarWatts.text = $"{solarKw:F2} kW";
            }
            if (_gridSolarFill != null)
            {
                _gridSolarFill.style.width = new Length(Mathf.Clamp01(solarKw / 3.6f) * 100f, LengthUnit.Percent);
            }
        }

        private void OpenStore(string title, string bannerClass, string bannerText, List<StoreItem> items)
        {
            _currentView = AppView.StoreDepot;
            HideAllViews();
            if (_viewStore == null) return;
            _viewStore.RemoveFromClassList("phone-app-view--hidden");

            if (_storeTitle != null) _storeTitle.text = title;
            if (_storeBanner != null)
            {
                _storeBanner.RemoveFromClassList("store-banner-depot");
                _storeBanner.RemoveFromClassList("store-banner-grocer");
                _storeBanner.RemoveFromClassList("store-banner-feed");
                _storeBanner.RemoveFromClassList("store-banner-lumber");
                _storeBanner.RemoveFromClassList("store-banner-auto");
                _storeBanner.RemoveFromClassList("store-banner-fuel");
                _storeBanner.RemoveFromClassList("store-banner-structures");
                _storeBanner.RemoveFromClassList("store-banner-equipment");
                _storeBanner.RemoveFromClassList("store-banner-furniture");
                _storeBanner.RemoveFromClassList("store-banner-voltvision");
                _storeBanner.RemoveFromClassList("store-banner-trailershack");
                _storeBanner.AddToClassList(bannerClass);
            }
            if (_storeBannerText != null) _storeBannerText.text = bannerText;

            _currentStoreAllItems = items;
            _storeSearchQuery = "";
            if (_storeSearchInput != null) _storeSearchInput.SetValueWithoutNotify("");
            FilterAndDisplayStoreItems();
            UpdateCartDisplay();
        }

        private void FilterAndDisplayStoreItems()
        {
            if (_currentStoreAllItems == null) return;

            string q = _storeSearchQuery?.Trim() ?? "";
            List<StoreItem> filtered;
            if (string.IsNullOrEmpty(q))
            {
                filtered = _currentStoreAllItems;
            }
            else
            {
                filtered = new List<StoreItem>();
                foreach (var item in _currentStoreAllItems)
                {
                    bool matchName = item.Name != null && item.Name.IndexOf(q, StringComparison.OrdinalIgnoreCase) >= 0;
                    bool matchCat = item.Category != null && item.Category.IndexOf(q, StringComparison.OrdinalIgnoreCase) >= 0;
                    bool matchId = item.Id != null && item.Id.IndexOf(q, StringComparison.OrdinalIgnoreCase) >= 0;
                    if (matchName || matchCat || matchId)
                    {
                        filtered.Add(item);
                    }
                }
            }

            PopulateStoreItems(filtered);

            if (filtered.Count == 0 && !string.IsNullOrEmpty(q))
            {
                var emptyLabel = new Label($"No items matching \"{_storeSearchQuery}\"");
                emptyLabel.AddToClassList("store-empty-search-label");
                _storeItemsContainer.Add(emptyLabel);
            }
        }

        private void PopulateStoreItems(List<StoreItem> items)
        {
            if (_storeItemsContainer == null) return;
            _storeItemsContainer.Clear();

            foreach (var item in items)
            {
                var card = new VisualElement();
                card.AddToClassList("store-item-card");

                var left = new VisualElement();
                left.AddToClassList("store-item-left");

                var iconBox = new VisualElement();
                iconBox.AddToClassList("store-item-icon-box");
                ApplyItemIcon(iconBox, item.IconGlyph, item.Id);

                var info = new VisualElement();
                info.AddToClassList("store-item-info");
                var nameLabel = new Label(item.Name);
                nameLabel.AddToClassList("store-item-name");
                var priceLabel = new Label($"${item.Price:F2} / {item.Unit}");
                priceLabel.AddToClassList("store-item-price");
                info.Add(nameLabel);
                info.Add(priceLabel);

                left.Add(iconBox);
                left.Add(info);

                var buyBtn = new Button();
                buyBtn.AddToClassList("store-item-buy-btn");
                buyBtn.text = "+ Add";
                string itemId = item.Id;
                buyBtn.clicked += () =>
                {
                    if (!_cart.ContainsKey(itemId)) _cart[itemId] = 0;
                    _cart[itemId]++;
                    UpdateCartDisplay();
                };

                card.Add(left);
                card.Add(buyBtn);
                _storeItemsContainer.Add(card);
            }
        }

        private void UpdateCartDisplay()
        {
            int totalCount = 0;
            float totalPrice = 0f;

            var allItems = GetAllCatalogItems();
            foreach (var pair in _cart)
            {
                totalCount += pair.Value;
                if (allItems.TryGetValue(pair.Key, out var item))
                {
                    totalPrice += item.Price * pair.Value;
                }
            }

            if (_storeCartCount != null) _storeCartCount.text = $"Items in Cart: {totalCount}";
            if (_storeCartTotal != null) _storeCartTotal.text = $"Total: ${totalPrice:F2}";
        }

        private void HandleCheckout()
        {
            int totalCount = 0;
            float totalPrice = 0f;
            var allItems = GetAllCatalogItems();
            foreach (var pair in _cart)
            {
                totalCount += pair.Value;
                if (allItems.TryGetValue(pair.Key, out var item))
                {
                    totalPrice += item.Price * pair.Value;
                }
            }

            if (totalCount == 0)
            {
                _showModalCallback?.Invoke("Cart Empty", "Your order cart is currently empty. Add items to place a homestead delivery!", null, null);
                return;
            }

            _showModalCallback?.Invoke(
                "Confirm Homestead Delivery",
                $"Order {totalCount} item(s) for a total of ${totalPrice:F2}?\nDelivery will arrive at the homestead drop pallet.",
                () =>
                {
                    if (!HudState.Active.SpendMoney(totalPrice))
                    {
                        _showModalCallback?.Invoke("Insufficient Funds", $"Your account balance (${HudState.Active.Money:F2}) is insufficient to complete this order of ${totalPrice:F2}.\nConsider taking out a farm micro-loan at First Homestead Bank.", null, null);
                        ToastNotificationSystem.ShowError("Payment Declined", $"Insufficient funds for ${totalPrice:F2} order.");
                        return;
                    }
                    Debug.Log($"<color=green>[Phone Delivery]</color> Order placed successfully! Paid ${totalPrice:F2} for {totalCount} items.");
                    ToastNotificationSystem.ShowSuccess("Delivery Dispatched", $"Your order of {totalCount} item(s) (${totalPrice:F2}) is on its way to the homestead drop pallet!");
                    _cart.Clear();
                    UpdateCartDisplay();
                },
                null
            );
        }

        // =========================================================================
        // BANKING ENGINE (FIRST HOMESTEAD BANK)
        // =========================================================================

        public void UpdateBankDisplay()
        {
            var state = HudState.Active;
            if (_bankBalanceText != null)
            {
                _bankBalanceText.text = $"${state.Money:N2}";
            }
            if (_bankLoanDebtText != null)
            {
                _bankLoanDebtText.text = $"${state.LoanDebt:N2}";
            }
            if (_bankDailyInterestText != null)
            {
                float dailyInterest = (state.LoanDebt * HudState.LoanInterestRate) / 365f;
                _bankDailyInterestText.text = $"Daily Interest: ${dailyInterest:F2} / day • 3.5% APR";
            }
        }

        private void BorrowLoan(float amount)
        {
            _showModalCallback?.Invoke(
                "Approve Loan Advance",
                $"Take out an advance of ${amount:N0} from First Homestead Bank at 3.5% APR?\nFunds will be credited immediately to your checking balance.",
                () =>
                {
                    HudState.Active.TakeLoan(amount);
                    UpdateBankDisplay();
                    Debug.Log($"<color=cyan>[Bank]</color> Borrowed ${amount:N0}. Total debt now: ${HudState.Active.LoanDebt:N2}");
                    ToastNotificationSystem.ShowInfo("Loan Deposited", $"${amount:N0} advance transferred to your homestead checking balance.");
                },
                null
            );
        }

        private void RepayLoan(float amount)
        {
            var state = HudState.Active;
            if (state.LoanDebt <= 0f)
            {
                _showModalCallback?.Invoke("No Active Debt", "You do not currently have any outstanding loan balance.", null, null);
                return;
            }

            float payAmount = Mathf.Min(amount, state.LoanDebt);
            if (state.Money < payAmount)
            {
                _showModalCallback?.Invoke("Insufficient Funds", $"You need ${payAmount:N2} to make this repayment, but your balance is only ${state.Money:N2}.", null, null);
                return;
            }

            _showModalCallback?.Invoke(
                "Confirm Loan Repayment",
                $"Pay ${payAmount:N2} towards your outstanding loan principal of ${state.LoanDebt:N2}?",
                () =>
                {
                    if (HudState.Active.RepayLoan(payAmount))
                    {
                        UpdateBankDisplay();
                        Debug.Log($"<color=green>[Bank]</color> Repaid ${payAmount:N2}. Remaining debt: ${HudState.Active.LoanDebt:N2}");
                        ToastNotificationSystem.ShowSuccess("Loan Payment Received", $"Paid ${payAmount:N2} towards loan principal. Outstanding debt: ${HudState.Active.LoanDebt:N2}");
                    }
                },
                null
            );
        }

        // =========================================================================
        // PLAYER MARKETPLACE ENGINE (HOMESTEAD EXCHANGE)
        // =========================================================================

        private void SwitchMarketTab(bool showBuy)
        {
            if (showBuy)
            {
                _marketTabBuyBtn?.AddToClassList("market-tab-btn--active");
                _marketTabSellBtn?.RemoveFromClassList("market-tab-btn--active");
                _marketBuyScroll?.RemoveFromClassList("phone-app-scroll--hidden");
                _marketSellScroll?.AddToClassList("phone-app-scroll--hidden");
            }
            else
            {
                _marketTabBuyBtn?.RemoveFromClassList("market-tab-btn--active");
                _marketTabSellBtn?.AddToClassList("market-tab-btn--active");
                _marketBuyScroll?.AddToClassList("phone-app-scroll--hidden");
                _marketSellScroll?.RemoveFromClassList("phone-app-scroll--hidden");
            }
        }

        private void OpenMarket()
        {
            SwitchMarketTab(true);
            PopulateMarketBuy();
            PopulateMarketSell();
        }

        private void PopulateMarketBuy()
        {
            if (_marketBuyContainer == null) return;
            _marketBuyContainer.Clear();

            var listings = GetCommunityListings();
            foreach (var item in listings)
            {
                var card = new VisualElement();
                card.AddToClassList("store-item-card");

                var left = new VisualElement();
                left.AddToClassList("store-item-left");

                var iconBox = new VisualElement();
                iconBox.AddToClassList("store-item-icon-box");
                ApplyItemIcon(iconBox, item.IconGlyph, item.Id);

                var info = new VisualElement();
                info.AddToClassList("store-item-info");
                var nameLabel = new Label(item.Name);
                nameLabel.AddToClassList("store-item-name");
                var priceLabel = new Label($"${item.Price:F2} • {item.Category}");
                priceLabel.AddToClassList("store-item-price");
                info.Add(nameLabel);
                info.Add(priceLabel);

                left.Add(iconBox);
                left.Add(info);

                var buyBtn = new Button();
                buyBtn.AddToClassList("store-item-buy-btn");
                buyBtn.text = "Buy";
                var listing = item;
                buyBtn.clicked += () =>
                {
                    _showModalCallback?.Invoke(
                        "Purchase Player Listing",
                        $"Buy {listing.Name} from local homesteader for ${listing.Price:F2}?",
                        () =>
                        {
                            if (!HudState.Active.SpendMoney(listing.Price))
                            {
                                _showModalCallback?.Invoke("Insufficient Funds", "You do not have enough funds to purchase this listing.", null, null);
                                return;
                            }
                            Debug.Log($"<color=green>[Exchange]</color> Purchased {listing.Name} for ${listing.Price:F2}!");
                        },
                        null
                    );
                };

                card.Add(left);
                card.Add(buyBtn);
                _marketBuyContainer.Add(card);
            }
        }

        private void PopulateMarketSell()
        {
            if (_marketSellContainer == null) return;
            _marketSellContainer.Clear();

            var sellables = GetPlayerSellables();
            foreach (var item in sellables)
            {
                var card = new VisualElement();
                card.AddToClassList("store-item-card");

                var left = new VisualElement();
                left.AddToClassList("store-item-left");

                var iconBox = new VisualElement();
                iconBox.AddToClassList("store-item-icon-box");
                ApplyItemIcon(iconBox, item.IconGlyph, item.Id);

                var info = new VisualElement();
                info.AddToClassList("store-item-info");
                var nameLabel = new Label(item.Name);
                nameLabel.AddToClassList("store-item-name");
                var priceLabel = new Label($"Sell for ${item.Price:F2} / {item.Unit}");
                priceLabel.AddToClassList("store-item-price");
                info.Add(nameLabel);
                info.Add(priceLabel);

                left.Add(iconBox);
                left.Add(info);

                var sellBtn = new Button();
                sellBtn.AddToClassList("store-item-buy-btn");
                sellBtn.text = "Sell";
                var sellItem = item;
                sellBtn.clicked += () =>
                {
                    _showModalCallback?.Invoke(
                        "Sell Homestead Goods",
                        $"Sell 1x {sellItem.Name} to the local market exchange for +${sellItem.Price:F2}?",
                        () =>
                        {
                            HudState.Active.AddMoney(sellItem.Price);
                            Debug.Log($"<color=green>[Exchange]</color> Sold {sellItem.Name} for +${sellItem.Price:F2}!");
                        },
                        null
                    );
                };

                card.Add(left);
                card.Add(sellBtn);
                _marketSellContainer.Add(card);
            }
        }

        private static List<StoreItem> GetCommunityListings()
        {
            return new List<StoreItem>
            {
                new StoreItem { Id = "player_truffle_oil", Name = "Artisan Truffle Oil (500ml)", Category = "By: FarmerDan", Price = 45.00f, IconGlyph = "🍄", Unit = "bottle" },
                new StoreItem { Id = "player_wool_sweater", Name = "Hand-Knitted Wool Sweater", Category = "By: WoolCrafter", Price = 65.00f, IconGlyph = "🧶", Unit = "ea" },
                new StoreItem { Id = "player_smoked_salmon", Name = "Oak-Smoked Salmon Fillets (x5)", Category = "By: RiverFisher", Price = 38.00f, IconGlyph = "🐟", Unit = "pack" },
                new StoreItem { Id = "player_cured_leather", Name = "Tanned Goat Leather Roll", Category = "By: FrontierTannery", Price = 55.00f, IconGlyph = "📜", Unit = "roll" },
                new StoreItem { Id = "player_aged_cheese", Name = "Raw Cow Milk Cheddar Wheel", Category = "By: MeadowDairy", Price = 42.00f, IconGlyph = "🧀", Unit = "wheel" }
            };
        }

        private static List<StoreItem> GetPlayerSellables()
        {
            return new List<StoreItem>
            {
                new StoreItem { Id = "food_apple", Name = "Crisp Orchard Apples (x10)", Category = "Fruit", Price = 15.00f, IconGlyph = "🍎", Unit = "crate" },
                new StoreItem { Id = "mat_log_oak", Name = "Hewn Oak Timber Logs (x5)", Category = "Lumber", Price = 35.00f, IconGlyph = "🪵", Unit = "stack" },
                new StoreItem { Id = "food_truffle", Name = "Foraged Black Truffle", Category = "Gourmet", Price = 60.00f, IconGlyph = "🍄", Unit = "oz" },
                new StoreItem { Id = "mat_wool_fleece", Name = "Sheared Sheep Wool Fleece", Category = "Textiles", Price = 25.00f, IconGlyph = "🐑", Unit = "fleece" },
                new StoreItem { Id = "food_egg", Name = "Farm Fresh Eggs (x12)", Category = "Dairy", Price = 6.00f, IconGlyph = "🥚", Unit = "dozen" }
            };
        }

        // =========================================================================
        // REAL ASSET CATALOG ENGINE (STORECATALOGS.JSON)
        // =========================================================================

#pragma warning disable 0649
        [Serializable]
        private class CatalogDatabase
        {
            public List<StoreItemData> lumber;
            public List<StoreItemData> depot;
            public List<StoreItemData> grocer;
            public List<StoreItemData> feed;
            public List<StoreItemData> water;
            public List<StoreItemData> vehicles;
            public List<StoreItemData> equipment;
            public List<StoreItemData> livestock;
            public List<StoreItemData> furniture;
            public List<StoreItemData> voltvision;
            public List<StoreItemData> trailershack;
        }

        [Serializable]
        private class StoreItemData
        {
            public string id;
            public string name;
            public string category;
            public float price;
            public string unit;
            public string description;
            public string icon;
        }
#pragma warning restore 0649

        private static CatalogDatabase s_catalogDb;
        private static readonly Dictionary<string, List<StoreItem>> s_realStoreItems = new Dictionary<string, List<StoreItem>>();

        // ── Unified Store & Item Icon Engine ────────────────────────────────
        private static readonly Dictionary<string, Texture2D> s_itemIconCache = new Dictionary<string, Texture2D>(StringComparer.OrdinalIgnoreCase);
        private static Dictionary<string, string> s_iconFileMap;

        private static void EnsureIconFileMap()
        {
            if (s_iconFileMap != null) return;
            s_iconFileMap = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);

            var searchFolders = new List<string>();

            string resIcons = Path.Combine(Application.dataPath, "Resources", "Icons");
            if (Directory.Exists(resIcons)) searchFolders.Add(resIcons);

            string modsFolder = Path.Combine(Application.dataPath, "Mods");
            if (Directory.Exists(modsFolder)) searchFolders.Add(modsFolder);

            string streamingMods = Path.Combine(Application.streamingAssetsPath, "Mods");
            if (Directory.Exists(streamingMods)) searchFolders.Add(streamingMods);

            string persistentMods = Path.Combine(Application.persistentDataPath, "Mods");
            if (Directory.Exists(persistentMods)) searchFolders.Add(persistentMods);

            string assetsFolder = Path.GetFullPath(Path.Combine(Application.dataPath, "..", "..", "assets"));
            if (Directory.Exists(assetsFolder)) searchFolders.Add(assetsFolder);

            foreach (var folder in searchFolders)
            {
                try
                {
                    foreach (var file in Directory.GetFiles(folder, "*.png", SearchOption.AllDirectories))
                    {
                        string fn = Path.GetFileName(file);
                        string fnNoExt = Path.GetFileNameWithoutExtension(file);
                        if (!s_iconFileMap.ContainsKey(fn)) s_iconFileMap[fn] = file;
                        if (!s_iconFileMap.ContainsKey(fnNoExt)) s_iconFileMap[fnNoExt] = file;
                    }
                }
                catch (Exception ex)
                {
                    Debug.LogWarning("[PhoneController] Failed indexing icons in " + folder + ": " + ex.Message);
                }
            }
        }

        public static Texture2D GetItemIcon(string iconName, string itemId = null)
        {
            string key = !string.IsNullOrEmpty(iconName) ? iconName : itemId;
            if (string.IsNullOrEmpty(key)) return null;

            if (s_itemIconCache.TryGetValue(key, out var cached) && cached != null)
                return cached;

            string baseName = Path.GetFileNameWithoutExtension(key);

            // 1. Resources.Load
            Texture2D tex = Resources.Load<Texture2D>("Icons/" + baseName)
                         ?? Resources.Load<Texture2D>("AssetCatalog/" + baseName)
                         ?? Resources.Load<Texture2D>("HUDTree/KitSprites/" + baseName);

            if (tex == null && !string.IsNullOrEmpty(itemId))
            {
                string idBase = Path.GetFileNameWithoutExtension(itemId);
                tex = Resources.Load<Texture2D>("Icons/" + idBase)
                   ?? Resources.Load<Texture2D>("AssetCatalog/" + idBase);
            }

            // 2. Direct disk file fallback via indexed map
            if (tex == null)
            {
                EnsureIconFileMap();
                string filePath = null;
                if (!s_iconFileMap.TryGetValue(baseName, out filePath))
                {
                    if (!string.IsNullOrEmpty(itemId))
                    {
                        string idBase = Path.GetFileNameWithoutExtension(itemId);
                        s_iconFileMap.TryGetValue(idBase, out filePath);
                    }
                }

                if (!string.IsNullOrEmpty(filePath) && File.Exists(filePath))
                {
                    try
                    {
                        byte[] bytes = File.ReadAllBytes(filePath);
                        var diskTex = new Texture2D(128, 128, TextureFormat.RGBA32, false);
                        if (diskTex.LoadImage(bytes))
                        {
                            diskTex.name = baseName;
                            tex = diskTex;
                        }
                    }
                    catch (Exception ex)
                    {
                        Debug.LogWarning("[PhoneController] Failed loading icon bytes for " + filePath + ": " + ex.Message);
                    }
                }
            }

            if (tex != null)
            {
                s_itemIconCache[key] = tex;
                if (!string.IsNullOrEmpty(itemId)) s_itemIconCache[itemId] = tex;
            }

            return tex;
        }

        private static void ApplyItemIcon(VisualElement iconBox, string iconGlyphOrFile, string itemId)
        {
            if (iconBox == null) return;
            Texture2D tex = GetItemIcon(iconGlyphOrFile, itemId);
            if (tex != null)
            {
                iconBox.Clear();
                iconBox.style.backgroundImage = new StyleBackground(tex);
            }
            else
            {
                iconBox.style.backgroundImage = null;
                if (iconBox.childCount == 0)
                {
                    string fallback = (!string.IsNullOrEmpty(iconGlyphOrFile) && !iconGlyphOrFile.EndsWith(".png", StringComparison.OrdinalIgnoreCase))
                        ? iconGlyphOrFile
                        : "📦";
                    var glyph = new Label(fallback);
                    glyph.style.fontSize = 20;
                    iconBox.Add(glyph);
                }
            }
        }

        private static List<StoreItem> GetRealCatalogItems(string key)
        {
            if (s_realStoreItems.TryGetValue(key, out var list) && list != null && list.Count > 0)
                return list;

            EnsureCatalogLoaded();

            List<StoreItemData> dataList = null;
            if (s_catalogDb != null)
            {
                switch (key.ToLowerInvariant())
                {
                    case "lumber": dataList = s_catalogDb.lumber; break;
                    case "depot": dataList = s_catalogDb.depot; break;
                    case "grocer": dataList = s_catalogDb.grocer; break;
                    case "feed": dataList = s_catalogDb.feed; break;
                    case "water": dataList = s_catalogDb.water; break;
                    case "vehicles": dataList = s_catalogDb.vehicles; break;
                    case "equipment": dataList = s_catalogDb.equipment; break;
                    case "livestock": dataList = s_catalogDb.livestock; break;
                    case "furniture": dataList = s_catalogDb.furniture; break;
                    case "voltvision": dataList = s_catalogDb.voltvision; break;
                    case "trailershack": dataList = s_catalogDb.trailershack; break;
                }
            }

            var result = new List<StoreItem>();
            if (dataList != null)
            {
                foreach (var d in dataList)
                {
                    result.Add(new StoreItem
                    {
                        Id = d.id,
                        Name = d.name,
                        Category = d.category,
                        Price = d.price,
                        Unit = d.unit,
                        IconGlyph = d.icon
                    });
                }
            }
            s_realStoreItems[key] = result;
            return result;
        }

        private static void EnsureCatalogLoaded()
        {
            if (s_catalogDb != null) return;
            var jsonAsset = Resources.Load<TextAsset>("StoreCatalogs");
            if (jsonAsset != null && !string.IsNullOrEmpty(jsonAsset.text))
            {
                try
                {
                    s_catalogDb = JsonUtility.FromJson<CatalogDatabase>(jsonAsset.text);
                }
                catch (Exception ex)
                {
                    Debug.LogWarning("[PhoneController] JsonUtility failed: " + ex.Message);
                }
            }
        }

        private static List<StoreItem> GetLumberItems() => GetRealCatalogItems("lumber");
        private static List<StoreItem> GetDepotItems() => GetRealCatalogItems("depot");
        private static List<StoreItem> GetGrocerItems() => GetRealCatalogItems("grocer");
        private static List<StoreItem> GetFeedItems() => GetRealCatalogItems("feed");
        private static List<StoreItem> GetVehicleItems() => GetRealCatalogItems("vehicles");
        private static List<StoreItem> GetWaterItems() => GetRealCatalogItems("water");
        private static List<StoreItem> GetLivestockItems() => GetRealCatalogItems("livestock");
        private static List<StoreItem> GetEquipmentItems() => GetRealCatalogItems("equipment");
        private static List<StoreItem> GetDealershipItems() => GetRealCatalogItems("equipment");
        private static List<StoreItem> GetFurnitureItems() => GetRealCatalogItems("furniture");
        private static List<StoreItem> GetVoltvisionItems() => GetRealCatalogItems("voltvision");
        private static List<StoreItem> GetTrailerShackItems() => GetRealCatalogItems("trailershack");

        private static Dictionary<string, StoreItem> GetAllCatalogItems()
        {
            var dict = new Dictionary<string, StoreItem>();
            foreach (var item in GetLumberItems()) dict[item.Id] = item;
            foreach (var item in GetDepotItems()) dict[item.Id] = item;
            foreach (var item in GetGrocerItems()) dict[item.Id] = item;
            foreach (var item in GetFeedItems()) dict[item.Id] = item;
            foreach (var item in GetVehicleItems()) dict[item.Id] = item;
            foreach (var item in GetWaterItems()) dict[item.Id] = item;
            foreach (var item in GetLivestockItems()) dict[item.Id] = item;
            foreach (var item in GetEquipmentItems()) dict[item.Id] = item;
            foreach (var item in GetDealershipItems()) dict[item.Id] = item;
            foreach (var item in GetFurnitureItems()) dict[item.Id] = item;
            foreach (var item in GetVoltvisionItems()) dict[item.Id] = item;
            foreach (var item in GetTrailerShackItems()) dict[item.Id] = item;
            return dict;
        }

        private void UpdateAdminDisplay()
        {
            _isUpdatingAdminUI = true;
            try
            {
                UpdateAdminDayLabel();
                UpdateAdminTimeLabel();
                UpdateAdminVitalsDisplay();
                UpdateAdminUnitButtons();
                UpdateAdminResourcesDisplay();
                UpdateAdminWeatherButtons();
            }
            finally
            {
                _isUpdatingAdminUI = false;
            }
        }

        private void UpdateAdminWeatherButtons()
        {
            bool isAuto = !TimeSystem.Instance.IsWeatherOverridden;
            var w = TimeSystem.Instance.Weather;
            var snap = TimeSystem.Instance.Snapshot();
            var units = HudState.Active.Units;

            // Show live temperature + override status on the Auto button
            string tempStr = TimeSystem.FormatTemperature(snap.TemperatureC, units);
            string hiLo = TimeSystem.FormatHighLow(snap.TodayHighC, snap.TodayLowC, units);
            if (_adminWeatherAutoBtn != null)
                _adminWeatherAutoBtn.text = isAuto
                    ? $"🔄 Auto  {tempStr}  {hiLo}"
                    : $"🔄 Auto (override active)";

            SetChipActive(_adminWeatherAutoBtn, isAuto);
            SetChipActive(_adminWeatherSunnyBtn, w == HomesteaderWeather.Sunny);
            SetChipActive(_adminWeatherPartlyCloudyBtn, w == HomesteaderWeather.PartlyCloudy);
            SetChipActive(_adminWeatherCloudyBtn, w == HomesteaderWeather.Cloudy);
            SetChipActive(_adminWeatherRainBtn, w == HomesteaderWeather.Rain);
            SetChipActive(_adminWeatherThunderstormBtn, w == HomesteaderWeather.Thunderstorm);
            SetChipActive(_adminWeatherSnowBtn, w == HomesteaderWeather.Snow);
            SetChipActive(_adminWeatherBlizzardBtn, w == HomesteaderWeather.Blizzard);
            SetChipActive(_adminWeatherWindBtn, w == HomesteaderWeather.Wind);
            SetChipActive(_adminWeatherFogBtn, w == HomesteaderWeather.Fog);
        }

        private void UpdateAdminUnitButtons()
        {
            bool isImp = (HudState.Active.Units == UnitSystem.Imperial);
            const string activeClass = "admin-chip-btn--active";

            if (_adminUnitMetricBtn != null)
            {
                if (isImp) _adminUnitMetricBtn.RemoveFromClassList(activeClass);
                else if (!_adminUnitMetricBtn.ClassListContains(activeClass)) _adminUnitMetricBtn.AddToClassList(activeClass);
            }
            if (_adminUnitImperialBtn != null)
            {
                if (isImp && !_adminUnitImperialBtn.ClassListContains(activeClass)) _adminUnitImperialBtn.AddToClassList(activeClass);
                else if (!isImp) _adminUnitImperialBtn.RemoveFromClassList(activeClass);
            }
        }

        private void UpdateResAppData()
        {
            var state = HudState.Active;
            bool isImp = (state.Units == UnitSystem.Imperial);

            if (_resWaterText != null)
            {
                string cap = isImp ? $"{1000f * HudState.LitersToGallons:N0} gal" : "1,000 L";
                _resWaterText.text = $"{state.FormatWater()} / {cap}";
            }
            if (_resFuelText != null)
            {
                string dieselStr = isImp ? $"{state.FuelDisplay:0.#} gal Diesel" : $"{state.Fuel:0.#} L Diesel";
                _resFuelText.text = $"{dieselStr} • 250 Gal Propane";
            }
        }

        private static void SetChipActive(Button btn, bool active)
        {
            if (btn == null) return;
            const string activeClass = "admin-chip-btn--active";
            if (active)
            {
                if (!btn.ClassListContains(activeClass)) btn.AddToClassList(activeClass);
            }
            else
            {
                btn.RemoveFromClassList(activeClass);
            }
        }

        private void UpdateAdminDayLabel()
        {
            var snap = TimeSystem.Instance.Snapshot();
            if (_adminDayLabel != null)
            {
                _adminDayLabel.text = $"Day {snap.DayOfYear} ({snap.MonthName} {snap.DayOfMonth} • {snap.Season})";
            }
            if (_adminDaySlider != null)
            {
                _adminDaySlider.value = snap.DayOfYear;
            }

            if (_adminDaylightLabel != null)
            {
                _adminDaylightLabel.text = $"Daylight: {snap.DaylightHours:F1}h • Sunrise {WallClock.FormatWithAmPm(snap.SunriseMinute)}, Sunset {WallClock.FormatWithAmPm(snap.SunsetMinute)}";
            }
            if (_adminAstroLabel != null)
            {
                _adminAstroLabel.text = !string.IsNullOrEmpty(snap.AstronomicalMilestone)
                    ? $"★ {snap.AstronomicalMilestone}"
                    : TimeSystem.GetDaylightTrend(snap.DayOfYear);
            }

            SetChipActive(_adminSeasonWinterBtn, snap.Season == HomesteaderSeason.Winter);
            SetChipActive(_adminSeasonSpringBtn, snap.Season == HomesteaderSeason.Spring);
            SetChipActive(_adminSeasonSummerBtn, snap.Season == HomesteaderSeason.Summer);
            SetChipActive(_adminSeasonAutumnBtn, snap.Season == HomesteaderSeason.Autumn);

            SetChipActive(_adminJumpSpringEquinoxBtn, snap.DayOfYear == TimeConstants.SpringEquinoxDay);
            SetChipActive(_adminJumpSummerSolsticeBtn, snap.DayOfYear == TimeConstants.SummerSolsticeDay);
            SetChipActive(_adminJumpAutumnEquinoxBtn, snap.DayOfYear == TimeConstants.AutumnalEquinoxDay);
            SetChipActive(_adminJumpWinterSolsticeBtn, snap.DayOfYear == TimeConstants.WinterSolsticeDay);
        }

        private void UpdateAdminTimeLabel()
        {
            var snap = TimeSystem.Instance.Snapshot();
            if (_adminTimeLabel != null)
            {
                _adminTimeLabel.text = $"Time: {TimeSystem.Instance.GetWallClock()}";
            }
            if (_adminTimeSlider != null)
            {
                _adminTimeSlider.value = snap.MinuteOfDay;
            }
            if (_adminTimeIcon != null)
            {
                var tex = Resources.Load<Texture2D>("HUDTree/KitSprites/celestial/" + snap.CelestialIconId);
                if (tex != null)
                {
                    _adminTimeIcon.style.backgroundImage = new StyleBackground(tex);
                }
            }
        }

        private static void UpdateVitalLabel(Label label, string name, int val)
        {
            if (label == null) return;
            string sign = (val > 0) ? $"+{val}" : val.ToString();
            string desc = (val == 0) ? "Neutral" : (val > 0 ? "Positive" : "Deficit");
            label.text = $"{name}: {sign} ({desc})";
        }

        private void UpdateAdminVitalsDisplay()
        {
            int wellness = HudState.Active.GetVitalValue(VitalId.Wellness);
            int stamina = HudState.Active.GetVitalValue(VitalId.Stamina);
            int thirst = HudState.Active.GetVitalValue(VitalId.Thirst);
            int hunger = HudState.Active.GetVitalValue(VitalId.Hunger);

            UpdateVitalLabel(_adminVitalWellnessLabel, "Wellness", wellness);
            if (_adminVitalWellnessSlider != null) _adminVitalWellnessSlider.value = wellness;

            UpdateVitalLabel(_adminVitalStaminaLabel, "Stamina", stamina);
            if (_adminVitalStaminaSlider != null) _adminVitalStaminaSlider.value = stamina;

            UpdateVitalLabel(_adminVitalThirstLabel, "Thirst", thirst);
            if (_adminVitalThirstSlider != null) _adminVitalThirstSlider.value = thirst;

            UpdateVitalLabel(_adminVitalHungerLabel, "Hunger", hunger);
            if (_adminVitalHungerSlider != null) _adminVitalHungerSlider.value = hunger;
        }

        private void UpdateAdminResourcesDisplay()
        {
            var state = HudState.Active;
            bool isImp = (state.Units == UnitSystem.Imperial);

            if (_adminResWaterLabel != null)
                _adminResWaterLabel.text = isImp ? "Water (gal):" : "Water (L):";
            if (_adminResElecLabel != null)
                _adminResElecLabel.text = isImp ? "Electricity (kWh):" : "Electricity (MJ):";
            if (_adminResBandwidthLabel != null)
                _adminResBandwidthLabel.text = "Bandwidth (Mbps):";
            if (_adminResFuelLabel != null)
                _adminResFuelLabel.text = isImp ? "Fuel (gal):" : "Fuel (L):";
            if (_adminResMoneyLabel != null)
                _adminResMoneyLabel.text = "Cash ($):";

            float water = state.WaterDisplay;
            float elec = state.ElectricityDisplay;
            float bw = state.Bandwidth;
            float fuel = state.FuelDisplay;
            float money = state.Money;

            if (_adminResWaterInput != null && _adminResWaterInput.panel?.focusController?.focusedElement != _adminResWaterInput)
                _adminResWaterInput.value = water.ToString("F1");

            if (_adminResElecInput != null && _adminResElecInput.panel?.focusController?.focusedElement != _adminResElecInput)
                _adminResElecInput.value = elec.ToString("F2");

            if (_adminResBandwidthInput != null && _adminResBandwidthInput.panel?.focusController?.focusedElement != _adminResBandwidthInput)
                _adminResBandwidthInput.value = bw.ToString("F1");

            if (_adminResFuelInput != null && _adminResFuelInput.panel?.focusController?.focusedElement != _adminResFuelInput)
                _adminResFuelInput.value = fuel.ToString("F1");

            if (_adminResMoneyInput != null && _adminResMoneyInput.panel?.focusController?.focusedElement != _adminResMoneyInput)
                _adminResMoneyInput.value = money.ToString("F2");
        }

        // =========================================================================
        // ALMANAC APP IMPLEMENTATION
        // =========================================================================

        private static Texture2D GetWeatherTexture(string iconId)
        {
            if (string.IsNullOrEmpty(iconId)) return null;
            if (!s_weatherTextures.TryGetValue(iconId, out var tex) || tex == null)
            {
                tex = Resources.Load<Texture2D>("HUDTree/KitSprites/weather/" + iconId);
                s_weatherTextures[iconId] = tex;
            }
            return tex;
        }

        private void OpenAlmanac()
        {
            UpdateAlmanacDisplay();
        }

        private void SwitchAlmanacTab(bool weekly)
        {
            _isAlmanacWeeklyTab = weekly;
            const string activeClass = "almanac-tab-btn--active";
            const string hiddenClass = "phone-app-scroll--hidden";

            if (_almanacTabDailyBtn != null)
            {
                if (weekly) _almanacTabDailyBtn.RemoveFromClassList(activeClass);
                else if (!_almanacTabDailyBtn.ClassListContains(activeClass)) _almanacTabDailyBtn.AddToClassList(activeClass);
            }

            if (_almanacTabWeeklyBtn != null)
            {
                if (weekly && !_almanacTabWeeklyBtn.ClassListContains(activeClass)) _almanacTabWeeklyBtn.AddToClassList(activeClass);
                else if (!weekly) _almanacTabWeeklyBtn.RemoveFromClassList(activeClass);
            }

            if (_almanacDailyContainer != null)
            {
                if (weekly) _almanacDailyContainer.AddToClassList(hiddenClass);
                else _almanacDailyContainer.RemoveFromClassList(hiddenClass);
            }

            if (_almanacWeeklyContainer != null)
            {
                if (weekly) _almanacWeeklyContainer.RemoveFromClassList(hiddenClass);
                else _almanacWeeklyContainer.AddToClassList(hiddenClass);
            }
        }

        private void UpdateAlmanacDisplay()
        {
            int currentDay = TimeSystem.Instance.DayOfYear;
            _lastAlmanacDayRendered = currentDay;

            var snap = TimeSystem.Instance.Snapshot();

            // Update Today Banner
            if (_almanacTodayTitle != null)
            {
                _almanacTodayTitle.text = $"TODAY • Day {snap.DayOfYear} ({snap.MonthName} {snap.DayOfMonth} • {snap.Season})";
            }
            if (_almanacTodayDetails != null)
            {
                int moonAge = ((snap.DayOfYear - 1) % 28) + 1;
                string moonIcon = AlmanacSystem.GetMoonPhaseIcon(moonAge);
                string moonName = AlmanacSystem.GetMoonPhaseName(moonAge);
                string astro = !string.IsNullOrEmpty(snap.AstronomicalMilestone) ? $" • ★ {snap.AstronomicalMilestone}" : "";
                var units = HudState.Active.Units;
                string nowTemp = TimeSystem.FormatTemperature(snap.TemperatureC, units);
                string hiLoStr = TimeSystem.FormatHighLow(snap.TodayHighC, snap.TodayLowC, units);
                _almanacTodayDetails.text = $"🌡 {nowTemp} ({hiLoStr}) • ☀️ Sunrise {WallClock.FormatWithAmPm(snap.SunriseMinute)} • 🌙 Sunset {WallClock.FormatWithAmPm(snap.SunsetMinute)} ({snap.DaylightHours:F1}h) • {moonIcon} {moonName}{astro}";
            }

            // Populate Daily Forecasts (56 days = 8 weeks)
            if (_almanacDailyContainer != null)
            {
                _almanacDailyContainer.Clear();
                var dailyForecasts = AlmanacSystem.Instance.GetDailyForecasts(currentDay);

                foreach (var df in dailyForecasts)
                {
                    var card = new VisualElement();
                    card.AddToClassList("almanac-card");
                    if (df.RelativeDayOffset == 0) card.AddToClassList("almanac-card-today");

                    // Top row: Date & relative offset badge + optional Astro badge
                    var topRow = new VisualElement();
                    topRow.AddToClassList("almanac-card-top");

                    var dateBox = new VisualElement();
                    dateBox.AddToClassList("almanac-card-date-box");

                    string dateStr = $"Day {df.DayOfYear} • {df.MonthName} {df.DayOfMonth} ({df.DayOfWeekName.Substring(0, 3)})";
                    var dateLabel = new Label(dateStr);
                    dateLabel.AddToClassList("almanac-card-date");
                    dateBox.Add(dateLabel);

                    string offsetStr = (df.RelativeDayOffset == 0) ? "Today"
                        : (df.RelativeDayOffset == 1) ? "Tomorrow"
                        : $"+{df.RelativeDayOffset}d";
                    var offsetLabel = new Label(offsetStr);
                    offsetLabel.AddToClassList("almanac-card-offset");
                    dateBox.Add(offsetLabel);

                    topRow.Add(dateBox);

                    if (!string.IsNullOrEmpty(df.AstronomicalBadge))
                    {
                        var badge = new Label(df.AstronomicalBadge);
                        badge.AddToClassList("almanac-card-astro-badge");
                        topRow.Add(badge);
                    }

                    card.Add(topRow);

                    // Sun & Moon Row
                    var sunRow = new VisualElement();
                    sunRow.AddToClassList("almanac-card-sun-row");
                    var sunText = new Label($"☀️ Rise {WallClock.FormatWithAmPm(df.SunriseMinute)} • 🌙 Set {WallClock.FormatWithAmPm(df.SunsetMinute)} ({df.DaylightHours:F1}h) • {df.MoonIcon} {df.MoonPhaseName}");
                    sunText.AddToClassList("almanac-card-sun-text");
                    sunRow.Add(sunText);
                    card.Add(sunRow);

                    // Temperature pill
                    var tempRow = new VisualElement();
                    tempRow.AddToClassList("almanac-card-temp-row");
                    var tempPill = new VisualElement();
                    tempPill.AddToClassList("almanac-card-temp-pill");
                    var units2 = HudState.Active.Units;
                    var hiLabel = new Label("H: " + TimeSystem.FormatTemperature(df.HighTempC, units2));
                    hiLabel.AddToClassList("almanac-temp-high");
                    var loLabel = new Label("L: " + TimeSystem.FormatTemperature(df.LowTempC, units2));
                    loLabel.AddToClassList("almanac-temp-low");
                    tempPill.Add(hiLabel);
                    tempPill.Add(loLabel);
                    tempRow.Add(tempPill);
                    card.Add(tempRow);

                    // Weather Row
                    var weatherRow = new VisualElement();
                    weatherRow.AddToClassList("almanac-card-weather-row");

                    var weatherLeft = new VisualElement();
                    weatherLeft.AddToClassList("almanac-card-weather-left");

                    var wIcon = new VisualElement();
                    wIcon.AddToClassList("almanac-weather-icon");
                    var wTex = GetWeatherTexture(df.WeatherIconId);
                    if (wTex != null) wIcon.style.backgroundImage = new StyleBackground(wTex);
                    weatherLeft.Add(wIcon);

                    var wName = new Label(df.PredictedWeatherName);
                    wName.AddToClassList("almanac-weather-name");
                    weatherLeft.Add(wName);
                    weatherRow.Add(weatherLeft);

                    var confBadge = new Label(df.ConfidenceTier + " (" + df.ConfidencePercent + "%)");
                    confBadge.AddToClassList("almanac-conf-badge");
                    if (df.RelativeDayOffset == 0) confBadge.AddToClassList("almanac-conf-current");
                    else if (df.ConfidencePercent >= 90) confBadge.AddToClassList("almanac-conf-high");
                    else if (df.ConfidencePercent >= 70) confBadge.AddToClassList("almanac-conf-med");
                    else confBadge.AddToClassList("almanac-conf-low");

                    weatherRow.Add(confBadge);
                    card.Add(weatherRow);

                    _almanacDailyContainer.Add(card);
                }
            }

            // Populate Weekly Forecasts (24 weeks)
            if (_almanacWeeklyContainer != null)
            {
                _almanacWeeklyContainer.Clear();
                var weeklyForecasts = AlmanacSystem.Instance.GetWeeklyForecasts(currentDay);

                foreach (var wf in weeklyForecasts)
                {
                    var card = new VisualElement();
                    card.AddToClassList("almanac-card");

                    // Top row: Week index & date range
                    var topRow = new VisualElement();
                    topRow.AddToClassList("almanac-card-top");

                    var dateBox = new VisualElement();
                    dateBox.AddToClassList("almanac-card-date-box");

                    var weekLabel = new Label($"Week {wf.WeekIndex} • {wf.DateRangeText} ({wf.Season})");
                    weekLabel.AddToClassList("almanac-card-date");
                    dateBox.Add(weekLabel);
                    topRow.Add(dateBox);

                    card.Add(topRow);

                    // Sun metrics row
                    var sunRow = new VisualElement();
                    sunRow.AddToClassList("almanac-card-sun-row");
                    var sunText = new Label($"☀️ Avg Rise {WallClock.FormatWithAmPm(wf.AvgSunriseMinute)} • 🌙 Avg Set {WallClock.FormatWithAmPm(wf.AvgSunsetMinute)} ({wf.AvgDaylightHours:F1}h)");
                    sunText.AddToClassList("almanac-card-sun-text");
                    sunRow.Add(sunText);
                    card.Add(sunRow);

                    // Temperature pill
                    var wTempRow = new VisualElement();
                    wTempRow.AddToClassList("almanac-card-temp-row");
                    var wTempPill = new VisualElement();
                    wTempPill.AddToClassList("almanac-card-temp-pill");
                    var wUnits = HudState.Active.Units;
                    var wHiLabel = new Label("H: " + TimeSystem.FormatTemperature(wf.AvgHighTempC, wUnits));
                    wHiLabel.AddToClassList("almanac-temp-high");
                    var wLoLabel = new Label("L: " + TimeSystem.FormatTemperature(wf.AvgLowTempC, wUnits));
                    wLoLabel.AddToClassList("almanac-temp-low");
                    wTempPill.Add(wHiLabel);
                    wTempPill.Add(wLoLabel);
                    wTempRow.Add(wTempPill);
                    card.Add(wTempRow);

                    // Weather row
                    var weatherRow = new VisualElement();
                    weatherRow.AddToClassList("almanac-card-weather-row");

                    var weatherLeft = new VisualElement();
                    weatherLeft.AddToClassList("almanac-card-weather-left");

                    var wIcon = new VisualElement();
                    wIcon.AddToClassList("almanac-weather-icon");
                    var wTex = GetWeatherTexture(wf.WeatherIconId);
                    if (wTex != null) wIcon.style.backgroundImage = new StyleBackground(wTex);
                    weatherLeft.Add(wIcon);

                    var wName = new Label("Outlook: " + wf.DominantWeatherName);
                    wName.AddToClassList("almanac-weather-name");
                    weatherLeft.Add(wName);
                    weatherRow.Add(weatherLeft);

                    var confBadge = new Label("Seasonal Outlook (40%)");
                    confBadge.AddToClassList("almanac-conf-badge");
                    confBadge.AddToClassList("almanac-conf-season");
                    weatherRow.Add(confBadge);

                    card.Add(weatherRow);

                    // Seasonal Note
                    if (!string.IsNullOrEmpty(wf.SeasonalTrendNote))
                    {
                        var note = new Label("💡 " + wf.SeasonalTrendNote);
                        note.AddToClassList("almanac-weekly-note");
                        card.Add(note);
                    }

                    _almanacWeeklyContainer.Add(card);
                }
            }
        }

        // =========================================================================
        // MODS MANAGER APP IMPLEMENTATION
        // =========================================================================

        private void OpenMods()
        {
            EnsureModEntriesLoaded(forceRefresh: true);
            UpdateModsView();

            if (_modsSearchInput != null)
            {
                _modsSearchInput.UnregisterValueChangedCallback(OnModSearchChanged);
                _modsSearchInput.RegisterValueChangedCallback(OnModSearchChanged);
            }
        }

        private void HandleModsBack()
        {
            if (_selectedModCategory != null)
            {
                GoToModCategories();
            }
            else
            {
                ReturnHome();
            }
        }

        private void GoToModCategories()
        {
            _selectedModCategory = null;
            if (_modsSearchInput != null)
            {
                _modsSearchInput.SetValueWithoutNotify("");
            }
            _activeModSearchQuery = "";
            UpdateModsView();
        }

        private void OpenModCategory(string categoryName)
        {
            _selectedModCategory = categoryName;
            if (_modsSearchInput != null)
            {
                _modsSearchInput.SetValueWithoutNotify("");
            }
            _activeModSearchQuery = "";
            UpdateModsView();
        }

        private void OnModSearchChanged(ChangeEvent<string> evt)
        {
            _activeModSearchQuery = evt.newValue?.Trim().ToLowerInvariant() ?? "";
            UpdateModsView();
        }

        private void UpdateModsView()
        {
            EnsureModEntriesLoaded();

            bool isSearching = !string.IsNullOrEmpty(_activeModSearchQuery);

            if (isSearching)
            {
                if (_modsCategoriesContainer != null) _modsCategoriesContainer.style.display = DisplayStyle.None;
                if (_modsListContainer != null)
                {
                    _modsListContainer.RemoveFromClassList("phone-app-view--hidden");
                    _modsListContainer.style.display = DisplayStyle.Flex;
                }
                if (_modsCategoryNav != null)
                {
                    _modsCategoryNav.RemoveFromClassList("phone-app-view--hidden");
                    _modsCategoryNav.style.display = DisplayStyle.Flex;
                }
                if (_modsCategoryTitle != null)
                {
                    _modsCategoryTitle.text = string.IsNullOrEmpty(_selectedModCategory)
                        ? "Search Results"
                        : $"{_selectedModCategory} (Filtered)";
                }
                if (_modsCategoryToggleBtn != null)
                {
                    _modsCategoryToggleBtn.style.display = DisplayStyle.None;
                }

                PopulateModsList(_selectedModCategory, _activeModSearchQuery);
            }
            else if (_selectedModCategory == null)
            {
                if (_modsCategoriesContainer != null)
                {
                    _modsCategoriesContainer.RemoveFromClassList("phone-app-view--hidden");
                    _modsCategoriesContainer.style.display = DisplayStyle.Flex;
                }
                if (_modsListContainer != null)
                {
                    _modsListContainer.AddToClassList("phone-app-view--hidden");
                    _modsListContainer.style.display = DisplayStyle.None;
                }
                if (_modsCategoryNav != null)
                {
                    _modsCategoryNav.AddToClassList("phone-app-view--hidden");
                    _modsCategoryNav.style.display = DisplayStyle.None;
                }

                PopulateCategoriesView();
            }
            else
            {
                if (_modsCategoriesContainer != null)
                {
                    _modsCategoriesContainer.AddToClassList("phone-app-view--hidden");
                    _modsCategoriesContainer.style.display = DisplayStyle.None;
                }
                if (_modsListContainer != null)
                {
                    _modsListContainer.RemoveFromClassList("phone-app-view--hidden");
                    _modsListContainer.style.display = DisplayStyle.Flex;
                }
                if (_modsCategoryNav != null)
                {
                    _modsCategoryNav.RemoveFromClassList("phone-app-view--hidden");
                    _modsCategoryNav.style.display = DisplayStyle.Flex;
                }
                if (_modsCategoryTitle != null)
                {
                    _modsCategoryTitle.text = _selectedModCategory;
                }

                UpdateCategoryToggleButton();
                PopulateModsList(_selectedModCategory, null);
            }
        }

        private void UpdateCategoryToggleButton()
        {
            if (_modsCategoryToggleBtn == null || string.IsNullOrEmpty(_selectedModCategory)) return;

            var catMods = s_cachedModEntries.FindAll(m => string.Equals(m.Category, _selectedModCategory, StringComparison.OrdinalIgnoreCase));
            if (catMods.Count == 0)
            {
                _modsCategoryToggleBtn.style.display = DisplayStyle.None;
                return;
            }

            _modsCategoryToggleBtn.style.display = DisplayStyle.Flex;
            bool allDisabled = catMods.TrueForAll(m => m.IsDisabled);

            _modsCategoryToggleBtn.RemoveFromClassList("mod-toggle-btn--enabled");
            _modsCategoryToggleBtn.RemoveFromClassList("mod-toggle-btn--disabled");

            if (allDisabled)
            {
                _modsCategoryToggleBtn.AddToClassList("mod-toggle-btn--disabled");
                _modsCategoryToggleBtn.text = "Enable Category";
            }
            else
            {
                _modsCategoryToggleBtn.AddToClassList("mod-toggle-btn--enabled");
                _modsCategoryToggleBtn.text = "Disable Category";
            }
        }

        private void PopulateCategoriesView()
        {
            if (_modsCategoriesContainer == null) return;
            _modsCategoriesContainer.Clear();

            EnsureModEntriesLoaded();

            // Group mods by Category
            var categories = new Dictionary<string, List<ModItemEntry>>(StringComparer.OrdinalIgnoreCase);
            foreach (var mod in s_cachedModEntries)
            {
                string cat = !string.IsNullOrEmpty(mod.Category) ? mod.Category : "General";
                if (!categories.TryGetValue(cat, out var list))
                {
                    list = new List<ModItemEntry>();
                    categories[cat] = list;
                }
                list.Add(mod);
            }

            var sortedKeys = categories.Keys.OrderBy(k => k, StringComparer.OrdinalIgnoreCase).ToList();

            foreach (string catName in sortedKeys)
            {
                var catMods = categories[catName];
                int totalMods = catMods.Count;
                int enabledMods = catMods.Count(m => !m.IsDisabled);
                int totalAssets = catMods.Sum(m => m.AssetCount);
                bool allDisabled = totalMods > 0 && enabledMods == 0;

                var card = new VisualElement();
                card.AddToClassList("mods-category-card");

                // Left info
                var left = new VisualElement();
                left.AddToClassList("mods-category-card-left");

                var nameLabel = new Label(catName);
                nameLabel.AddToClassList("mods-category-card-name");

                string statusText = allDisabled
                    ? $"[Disabled] • {totalMods} {(totalMods == 1 ? "mod" : "mods")}"
                    : $"{totalMods} {(totalMods == 1 ? "mod" : "mods")} ({enabledMods} active) • {totalAssets} assets";
                var subLabel = new Label(statusText);
                subLabel.AddToClassList("mods-category-card-sub");

                left.Add(nameLabel);
                left.Add(subLabel);

                // Right controls
                var right = new VisualElement();
                right.AddToClassList("mods-category-card-right");

                var toggleBtn = new Button();
                toggleBtn.AddToClassList("mod-toggle-btn");
                if (allDisabled)
                {
                    toggleBtn.AddToClassList("mod-toggle-btn--disabled");
                    toggleBtn.text = "✕ Disabled";
                }
                else
                {
                    toggleBtn.AddToClassList("mod-toggle-btn--enabled");
                    toggleBtn.text = "✓ Enabled";
                }

                string currentCat = catName;
                toggleBtn.clicked += () => ToggleCategory(currentCat);

                var arrow = new Label("›");
                arrow.AddToClassList("mods-category-open-arrow");

                right.Add(toggleBtn);
                right.Add(arrow);

                card.Add(left);
                card.Add(right);

                // Click card (outside button) to drill into category
                card.RegisterCallback<ClickEvent>(evt =>
                {
                    if (evt.target == toggleBtn) return;
                    OpenModCategory(currentCat);
                });

                _modsCategoriesContainer.Add(card);
            }

            if (sortedKeys.Count == 0)
            {
                var emptyLabel = new Label("No mod categories discovered.");
                emptyLabel.style.color = new StyleColor(new Color(0.6f, 0.65f, 0.72f));
                emptyLabel.style.fontSize = 13;
                emptyLabel.style.paddingTop = 20;
                emptyLabel.style.alignSelf = Align.Center;
                _modsCategoriesContainer.Add(emptyLabel);
            }
        }

        private void PopulateModsList(string filterCategory, string searchQuery)
        {
            if (_modsListContainer == null) return;
            _modsListContainer.Clear();

            EnsureModEntriesLoaded();

            int matchCount = 0;
            foreach (var mod in s_cachedModEntries)
            {
                // Category Filter (if specified and not All)
                if (!string.IsNullOrEmpty(filterCategory) && !string.Equals(filterCategory, "All", StringComparison.OrdinalIgnoreCase))
                {
                    if (!string.Equals(mod.Category, filterCategory, StringComparison.OrdinalIgnoreCase))
                    {
                        continue;
                    }
                }

                // Search Query Filter
                if (!string.IsNullOrEmpty(searchQuery))
                {
                    bool matchesName = mod.Name != null && mod.Name.IndexOf(searchQuery, StringComparison.OrdinalIgnoreCase) >= 0;
                    bool matchesDesc = mod.Description != null && mod.Description.IndexOf(searchQuery, StringComparison.OrdinalIgnoreCase) >= 0;
                    bool matchesCat = mod.Category != null && mod.Category.IndexOf(searchQuery, StringComparison.OrdinalIgnoreCase) >= 0;
                    bool matchesId = mod.Id != null && mod.Id.IndexOf(searchQuery, StringComparison.OrdinalIgnoreCase) >= 0;
                    if (!matchesName && !matchesDesc && !matchesCat && !matchesId) continue;
                }

                matchCount++;
                var card = new VisualElement();
                card.AddToClassList("mod-card");

                // Header row
                var topRow = new VisualElement();
                topRow.AddToClassList("mod-card-top");

                var title = new Label(mod.Name);
                title.AddToClassList("mod-title");
                if (mod.IsDisabled)
                {
                    title.style.color = new StyleColor(new Color(0.65f, 0.7f, 0.78f));
                }
                topRow.Add(title);

                var badge = new Label(mod.IsDisabled ? "DISABLED" : "ENABLED");
                badge.AddToClassList("mod-badge");
                if (mod.IsDisabled)
                {
                    badge.AddToClassList("mod-badge--disabled");
                }
                else
                {
                    badge.AddToClassList("mod-badge--enabled");
                }
                topRow.Add(badge);
                card.Add(topRow);

                // Description
                var desc = new Label(mod.Description);
                desc.AddToClassList("mod-desc");
                card.Add(desc);

                // Meta row
                var metaRow = new VisualElement();
                metaRow.AddToClassList("mod-meta-row");

                var leftMeta = new Label($"Assets: {mod.AssetCount} items • v{mod.Version} • Category: {mod.Category}");
                var rightMeta = new Label($"By {mod.Author}");
                metaRow.Add(leftMeta);
                metaRow.Add(rightMeta);
                card.Add(metaRow);

                // Action Row (Folder info + Enable/Disable Toggle button)
                var actionRow = new VisualElement();
                actionRow.AddToClassList("mod-action-row");

                string folderName = !string.IsNullOrEmpty(mod.FolderPath) ? Path.GetFileName(mod.FolderPath) : mod.Id;
                var folderLabel = new Label($"📁 {folderName}");
                folderLabel.AddToClassList("mod-folder-label");
                actionRow.Add(folderLabel);

                var toggleBtn = new Button();
                toggleBtn.AddToClassList("mod-toggle-btn");
                if (mod.IsDisabled)
                {
                    toggleBtn.AddToClassList("mod-toggle-btn--disabled");
                    toggleBtn.text = "✕ Disabled";
                }
                else
                {
                    toggleBtn.AddToClassList("mod-toggle-btn--enabled");
                    toggleBtn.text = "✓ Enabled";
                }

                var targetMod = mod;
                toggleBtn.clicked += () => ToggleMod(targetMod, !targetMod.IsDisabled);

                actionRow.Add(toggleBtn);
                card.Add(actionRow);

                _modsListContainer.Add(card);
            }

            if (matchCount == 0)
            {
                var emptyLabel = new Label(!string.IsNullOrEmpty(searchQuery)
                    ? $"No mods matching \"{searchQuery}\"."
                    : "No mods in this category.");
                emptyLabel.style.color = new StyleColor(new Color(0.6f, 0.65f, 0.72f));
                emptyLabel.style.fontSize = 13;
                emptyLabel.style.paddingTop = 20;
                emptyLabel.style.alignSelf = Align.Center;
                _modsListContainer.Add(emptyLabel);
            }
        }

        private void ToggleMod(ModItemEntry mod, bool enable)
        {
            if (string.IsNullOrEmpty(mod.FolderPath) || !Directory.Exists(mod.FolderPath))
            {
                Debug.LogWarning($"[PhoneController] Cannot toggle mod '{mod.Name}', folder does not exist: {mod.FolderPath}");
                return;
            }

            string newPath = ModDiscovery.SetFolderDisabled(mod.FolderPath, !enable, msg => Debug.Log(msg));
            mod.FolderPath = newPath;
            mod.IsDisabled = !enable;

            EnsureModEntriesLoaded(forceRefresh: true);

            if (ModManager.Instance != null)
            {
                ModManager.Instance.LoadMods();
            }

            UpdateModsView();
        }

        private void ToggleCurrentCategory()
        {
            if (string.IsNullOrEmpty(_selectedModCategory)) return;
            ToggleCategory(_selectedModCategory);
        }

        private void ToggleCategory(string categoryName)
        {
            EnsureModEntriesLoaded();
            var catMods = s_cachedModEntries.FindAll(m => string.Equals(m.Category, categoryName, StringComparison.OrdinalIgnoreCase));
            if (catMods.Count == 0) return;

            bool allDisabled = catMods.TrueForAll(m => m.IsDisabled);
            bool targetDisable = !allDisabled; // if any is enabled, we disable; if all disabled, we enable

            // Check if there is a category parent folder
            string catFolderPath = catMods.Find(m => !string.IsNullOrEmpty(m.CategoryFolderPath))?.CategoryFolderPath;
            if (!string.IsNullOrEmpty(catFolderPath) && Directory.Exists(catFolderPath))
            {
                ModDiscovery.SetFolderDisabled(catFolderPath, targetDisable, msg => Debug.Log(msg));
            }
            else
            {
                // Toggle each mod folder in the category
                foreach (var m in catMods)
                {
                    if (!string.IsNullOrEmpty(m.FolderPath) && Directory.Exists(m.FolderPath))
                    {
                        ModDiscovery.SetFolderDisabled(m.FolderPath, targetDisable, msg => Debug.Log(msg));
                    }
                }
            }

            EnsureModEntriesLoaded(forceRefresh: true);

            if (ModManager.Instance != null)
            {
                ModManager.Instance.LoadMods();
            }

            UpdateModsView();
        }

        private static int CountModAssets(ModInfo info)
        {
            if (info == null || string.IsNullOrEmpty(info.RootPath)) return 1;
            try
            {
                string assetsSubdir = Path.Combine(info.RootPath, "assets");
                if (Directory.Exists(assetsSubdir))
                {
                    int count = 0;
                    foreach (var catDir in Directory.GetDirectories(assetsSubdir))
                    {
                        count += Directory.GetDirectories(catDir).Length;
                    }
                    if (count > 0) return count;
                }
            }
            catch { }
            return info.Manifest?.Contents != null && info.Manifest.Contents.Count > 0 ? info.Manifest.Contents.Count : 1;
        }

        private static void EnsureModEntriesLoaded(bool forceRefresh = false)
        {
            if (!forceRefresh && s_cachedModEntries != null && s_cachedModEntries.Count > 0) return;

            s_cachedModEntries = new List<ModItemEntry>();

            // 1. If ModManager is loaded, read from its LoadedMods
            if (ModManager.Instance != null && ModManager.Instance.LoadedMods.Count > 0)
            {
                foreach (var info in ModManager.Instance.LoadedMods)
                {
                    s_cachedModEntries.Add(new ModItemEntry
                    {
                        Id = info.Id,
                        Name = info.Manifest?.Name ?? ModDiscovery.StripDisabledSuffix(info.SourceName),
                        Category = !string.IsNullOrEmpty(info.Category) ? info.Category : "General",
                        Description = info.Manifest?.Description ?? "Custom community modification for Homesteader.",
                        Author = info.Manifest?.Author ?? "Homesteader Team",
                        Version = info.Manifest?.Version ?? "1.0.0",
                        AssetCount = CountModAssets(info),
                        FolderPath = info.RootPath,
                        IsDisabled = info.IsDisabled || ModDiscovery.IsDisabledName(info.SourceName) || ModDiscovery.IsPathDisabled(info.RootPath),
                        CategoryFolderPath = info.CategoryFolderPath,
                        IsCategoryDisabled = !string.IsNullOrEmpty(info.CategoryFolderPath) && ModDiscovery.IsDisabledName(Path.GetFileName(info.CategoryFolderPath))
                    });
                }
                return;
            }

            // 2. Discover from disk directly
            var roots = new List<string>();
            var seenRoots = new HashSet<string>(StringComparer.OrdinalIgnoreCase);

            void AddRoot(string p)
            {
                if (string.IsNullOrWhiteSpace(p)) return;
                try
                {
                    string full = Path.GetFullPath(p);
                    if (seenRoots.Add(full) && Directory.Exists(full)) roots.Add(full);
                }
                catch { }
            }

            AddRoot(Path.Combine(Application.dataPath, "Mods"));
            try
            {
                AddRoot(Path.GetFullPath(Path.Combine(Application.dataPath, "../../mods")));
                AddRoot(Path.Combine(Directory.GetCurrentDirectory(), "mods"));
                AddRoot(Path.Combine(Application.persistentDataPath, "Mods"));
                AddRoot(Path.Combine(Application.streamingAssetsPath, "Mods"));
            }
            catch { }

            var seenIds = new HashSet<string>(StringComparer.OrdinalIgnoreCase);

            foreach (string root in roots)
            {
                var discovered = ModDiscovery.Discover(root);
                foreach (var mod in discovered)
                {
                    string manifestPath = Path.Combine(mod.RootPath, ModManifestParser.ManifestFileNameFor);
                    if (File.Exists(manifestPath))
                    {
                        try
                        {
                            string json = File.ReadAllText(manifestPath);
                            mod.Manifest = ModManifestParser.Parse(json, manifestPath, mod);
                        }
                        catch { }
                    }

                    string category = mod.Category;
                    if (string.IsNullOrEmpty(category) && mod.Manifest != null)
                    {
                        category = mod.Manifest.Raw.Get("category").AsString();
                        if (string.IsNullOrEmpty(category)) category = mod.Manifest.Raw.Get("namespace").AsString();
                        if (string.IsNullOrEmpty(category) && mod.Manifest.Contents.Count > 0)
                        {
                            category = mod.Manifest.Contents[0].Group;
                            if (string.IsNullOrEmpty(category)) category = mod.Manifest.Contents[0].Type;
                        }
                    }
                    if (string.IsNullOrEmpty(category))
                    {
                        string folder = ModDiscovery.StripDisabledSuffix(mod.SourceName);
                        category = folder.StartsWith("mod_", StringComparison.OrdinalIgnoreCase)
                            ? folder.Substring(4)
                            : folder;
                    }
                    if (!string.IsNullOrEmpty(category))
                    {
                        category = char.ToUpperInvariant(category[0]) + category.Substring(1);
                    }

                    string id = mod.Id;
                    if (seenIds.Add(id))
                    {
                        s_cachedModEntries.Add(new ModItemEntry
                        {
                            Id = id,
                            Name = mod.Manifest?.Name ?? ModDiscovery.StripDisabledSuffix(mod.SourceName),
                            Category = category,
                            Description = mod.Manifest?.Description ?? "Custom community modification for Homesteader.",
                            Author = mod.Manifest?.Author ?? "Homesteader Team",
                            Version = mod.Manifest?.Version ?? "1.0.0",
                            AssetCount = CountModAssets(mod),
                            FolderPath = mod.RootPath,
                            IsDisabled = mod.IsDisabled || ModDiscovery.IsDisabledName(mod.SourceName) || ModDiscovery.IsPathDisabled(mod.RootPath),
                            CategoryFolderPath = mod.CategoryFolderPath,
                            IsCategoryDisabled = !string.IsNullOrEmpty(mod.CategoryFolderPath) && ModDiscovery.IsDisabledName(Path.GetFileName(mod.CategoryFolderPath))
                        });
                    }
                }
            }

            if (s_cachedModEntries.Count == 0)
            {
                s_cachedModEntries = GetDefaultFallbackModEntries();
            }
        }

        private static List<ModItemEntry> GetDefaultFallbackModEntries()
        {
            return new List<ModItemEntry>
            {
                new ModItemEntry { Id = "mod_building", Name = "Building & Construction", Category = "Building", Description = "Walls, roofs, timber trusses, windows, doors, and architectural framing components.", Author = "Homesteader Team", Version = "1.0.0", AssetCount = 85 },
                new ModItemEntry { Id = "mod_materials", Name = "Raw Materials & Ores", Category = "Materials", Description = "Milled timber studs, quarried stones, raw ores, ingots, and building composites.", Author = "Homesteader Team", Version = "1.0.0", AssetCount = 69 },
                new ModItemEntry { Id = "mod_tools", Name = "Hand & Power Tools", Category = "Tools", Description = "Axes, framing hammers, hand saws, hoes, pickaxes, shovels, and mechanic wrenches.", Author = "Homesteader Team", Version = "1.0.0", AssetCount = 53 },
                new ModItemEntry { Id = "mod_appliances", Name = "Appliances Pack", Category = "Appliances", Description = "Household and workshop appliances, refrigeration, laundry, and heating equipment.", Author = "Homesteader Team", Version = "1.0.0", AssetCount = 42 },
                new ModItemEntry { Id = "mod_electricity", Name = "Electrical & Solar Grid", Category = "Electricity", Description = "Photovoltaic solar panels, battery banks, inverters, power meters, and wiring.", Author = "Homesteader Team", Version = "1.0.0", AssetCount = 37 },
                new ModItemEntry { Id = "mod_water", Name = "Plumbing & Water Storage", Category = "Water", Description = "Poly rainwater cisterns, jet well pumps, filtration systems, and water distribution.", Author = "Homesteader Team", Version = "1.0.0", AssetCount = 31 },
                new ModItemEntry { Id = "mod_logging", Name = "Timber & Forestry", Category = "Logging", Description = "Chainsaws, felling wedges, timber jacks, peaveys, and forestry equipment.", Author = "Homesteader Team", Version = "1.0.0", AssetCount = 30 },
                new ModItemEntry { Id = "mod_vehicles", Name = "Vehicles & Utility Haulers", Category = "Vehicles", Description = "Homestead utility tractors, flatbed trailers, ATVs, and heavy cargo haulers.", Author = "Homesteader Team", Version = "1.0.0", AssetCount = 23 },
                new ModItemEntry { Id = "mod_fishing", Name = "Fishing & Tackle", Category = "Fishing", Description = "Freshwater rods, reels, cast nets, tackle boxes, and caught fish.", Author = "Homesteader Team", Version = "1.0.0", AssetCount = 19 },
                new ModItemEntry { Id = "mod_food", Name = "Pantry & Provisions", Category = "Food", Description = "Harvested orchard fruits, farm produce, dairy, canned goods, and pantry staples.", Author = "Homesteader Team", Version = "1.0.0", AssetCount = 24 },
                new ModItemEntry { Id = "mod_waste", Name = "Sanitation & Waste Processing", Category = "Waste", Description = "Composters, septic tanks, refuse collection bins, and scrap processing equipment.", Author = "Homesteader Team", Version = "1.0.0", AssetCount = 19 },
                new ModItemEntry { Id = "mod_fuel", Name = "Fuel & Heating", Category = "Fuel", Description = "Diesel containers, bulk propane tanks, cordwood stacks, and fuel storage.", Author = "Homesteader Team", Version = "1.0.0", AssetCount = 17 },
                new ModItemEntry { Id = "mod_internet", Name = "Telecom & Telemetry", Category = "Internet", Description = "Satellite dishes, cellular routers, telemetry sensors, and communication hardware.", Author = "Homesteader Team", Version = "1.0.0", AssetCount = 16 },
                new ModItemEntry { Id = "mod_ingredients", Name = "Culinary Ingredients", Category = "Ingredients", Description = "Flours, yeasts, seasonings, culinary oils, and raw cooking staples.", Author = "Homesteader Team", Version = "1.0.0", AssetCount = 15 },
                new ModItemEntry { Id = "mod_farming", Name = "Farming & Crops", Category = "Farming", Description = "Seed packets, organic fertilizers, soil amendments, and planting supplies.", Author = "Homesteader Team", Version = "1.0.0", AssetCount = 10 },
                new ModItemEntry { Id = "mod_structures", Name = "Pre-Fab Outbuildings", Category = "Structures", Description = "Pre-assembled storage sheds, coops, and homestead utility structures.", Author = "Homesteader Team", Version = "1.0.0", AssetCount = 9 },
                new ModItemEntry { Id = "mod_ranching", Name = "Livestock & Ranch Supplies", Category = "Ranching", Description = "Alfalfa hay bales, mineral salt blocks, shearing equipment, and animal care supplies.", Author = "Homesteader Team", Version = "1.0.0", AssetCount = 8 },
                new ModItemEntry { Id = "example_lavender_homestead", Name = "Lavender Homestead", Category = "Example", Description = "Adds lavender fields, a lavender drying shed, and lavender tea.", Author = "Homesteader Team", Version = "1.0.0", AssetCount = 3 }
            };
        }
    }
}
