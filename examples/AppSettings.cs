using System;
using System.IO;
using System.Text.Json;

namespace SampleApplication
{
    /// <summary>
    /// Application settings model
    /// </summary>
    public class AppSettings
    {
        /// <summary>
        /// Application name
        /// </summary>
        public string ApplicationName { get; set; } = "Sample Application";

        /// <summary>
        /// Whether to use dark theme
        /// </summary>
        public bool UseDarkTheme { get; set; } = false;

        /// <summary>
        /// Window width
        /// </summary>
        public double WindowWidth { get; set; } = 800;

        /// <summary>
        /// Window height
        /// </summary>
        public double WindowHeight { get; set; } = 450;

        /// <summary>
        /// Whether to show welcome screen on startup
        /// </summary>
        public bool ShowWelcomeScreen { get; set; } = true;

        /// <summary>
        /// Log level
        /// </summary>
        public LogLevel LogLevel { get; set; } = LogLevel.Info;

        /// <summary>
        /// Auto-save interval in minutes
        /// </summary>
        public int AutoSaveIntervalMinutes { get; set; } = 5;
    }

    /// <summary>
    /// Log level enum
    /// </summary>
    public enum LogLevel
    {
        /// <summary>
        /// Debug level logging
        /// </summary>
        Debug,

        /// <summary>
        /// Info level logging
        /// </summary>
        Info,

        /// <summary>
        /// Warning level logging
        /// </summary>
        Warning,

        /// <summary>
        /// Error level logging
        /// </summary>
        Error
    }

    /// <summary>
    /// Manager for application settings
    /// </summary>
    public class SettingsManager
    {
        private readonly string _settingsFilePath;

        /// <summary>
        /// Constructor
        /// </summary>
        public SettingsManager()
        {
            // Get settings directory
            var appDataPath = Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData);
            var appDataDir = Path.Combine(appDataPath, "SampleApplication");

            // Create directory if it doesn't exist
            if (!Directory.Exists(appDataDir))
            {
                Directory.CreateDirectory(appDataDir);
            }

            // Set settings file path
            _settingsFilePath = Path.Combine(appDataDir, "settings.json");
        }

        /// <summary>
        /// Load settings from file
        /// </summary>
        public AppSettings LoadSettings()
        {
            try
            {
                // Check if settings file exists
                if (!File.Exists(_settingsFilePath))
                {
                    // Return default settings if file doesn't exist
                    return new AppSettings();
                }

                // Read settings file
                var json = File.ReadAllText(_settingsFilePath);

                // Deserialize settings
                var settings = JsonSerializer.Deserialize<AppSettings>(json);

                // Return deserialized settings or default if null
                return settings ?? new AppSettings();
            }
            catch (Exception)
            {
                // Return default settings on error
                return new AppSettings();
            }
        }

        /// <summary>
        /// Save settings to file
        /// </summary>
        public void SaveSettings(AppSettings settings)
        {
            try
            {
                // Use default settings if null
                settings ??= new AppSettings();

                // Serialize settings
                var options = new JsonSerializerOptions { WriteIndented = true };
                var json = JsonSerializer.Serialize(settings, options);

                // Write settings to file
                File.WriteAllText(_settingsFilePath, json);
            }
            catch (Exception)
            {
                // Handle error
                Console.WriteLine("Error saving settings");
            }
        }
    }

    /// <summary>
    /// Dialog for editing settings
    /// </summary>
    public class SettingsDialog : System.Windows.Window
    {
        /// <summary>
        /// Settings being edited
        /// </summary>
        public AppSettings Settings { get; private set; }

        /// <summary>
        /// Constructor
        /// </summary>
        public SettingsDialog(AppSettings settings)
        {
            // Clone settings
            Settings = new AppSettings
            {
                ApplicationName = settings.ApplicationName,
                UseDarkTheme = settings.UseDarkTheme,
                WindowWidth = settings.WindowWidth,
                WindowHeight = settings.WindowHeight,
                ShowWelcomeScreen = settings.ShowWelcomeScreen,
                LogLevel = settings.LogLevel,
                AutoSaveIntervalMinutes = settings.AutoSaveIntervalMinutes
            };

            // Initialize dialog
            Title = "Settings";
            Width = 400;
            Height = 300;

            // For demo purposes, we're not implementing the full dialog UI
        }
    }
}