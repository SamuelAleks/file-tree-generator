using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using System.Windows.Media;

namespace SampleApplication
{
    /// <summary>
    /// Interaction logic for MainWindow.xaml
    /// </summary>
    public partial class MainWindow : Window
    {
        // Private fields
        private readonly UserService _userService;
        private readonly SettingsManager _settingsManager;
        private bool _isDirty = false;

        // Properties
        public string ApplicationTitle { get; set; } = "Sample Application";

        public List<User> Users { get; private set; }

        public User CurrentUser
        {
            get => _currentUser;
            set
            {
                _currentUser = value;
                OnUserChanged(value);
            }
        }
        private User _currentUser;

        /// <summary>
        /// Constructor for the Main Window
        /// </summary>
        public MainWindow()
        {
            InitializeComponent();

            // Initialize services
            _userService = new UserService();
            _settingsManager = new SettingsManager();

            // Set data context
            DataContext = this;

            // Load initial data
            LoadData();
        }

        /// <summary>
        /// Load data from services
        /// </summary>
        private async void LoadData()
        {
            try
            {
                // Load settings
                var settings = _settingsManager.LoadSettings();
                ApplySettings(settings);

                // Load users
                Users = await _userService.GetUsersAsync();

                // Set initial user if available
                if (Users.Any())
                {
                    CurrentUser = Users.First();
                }

                // Update UI
                RefreshUI();
            }
            catch (Exception ex)
            {
                HandleError(ex, "Error loading data");
            }
        }

        /// <summary>
        /// Apply application settings
        /// </summary>
        private void ApplySettings(AppSettings settings)
        {
            if (settings == null) return;

            // Apply theme
            if (settings.UseDarkTheme)
            {
                ApplyDarkTheme();
            }
            else
            {
                ApplyLightTheme();
            }

            // Apply window size and position
            if (settings.WindowWidth > 0)
            {
                Width = settings.WindowWidth;
            }

            if (settings.WindowHeight > 0)
            {
                Height = settings.WindowHeight;
            }

            // Set application title
            ApplicationTitle = settings.ApplicationName ?? "Sample Application";
            Title = ApplicationTitle;
        }

        /// <summary>
        /// Apply dark theme to application
        /// </summary>
        private void ApplyDarkTheme()
        {
            var darkBrush = new SolidColorBrush(Colors.DarkGray);
            var lightBrush = new SolidColorBrush(Colors.White);

            // Apply theme colors
            Background = darkBrush;
            Foreground = lightBrush;

            // Update status
            StatusText.Text = "Dark theme applied";
        }

        /// <summary>
        /// Apply light theme to application
        /// </summary>
        private void ApplyLightTheme()
        {
            var whiteBrush = new SolidColorBrush(Colors.White);
            var blackBrush = new SolidColorBrush(Colors.Black);

            // Apply theme colors
            Background = whiteBrush;
            Foreground = blackBrush;

            // Update status
            StatusText.Text = "Light theme applied";
        }

        /// <summary>
        /// Refresh the UI
        /// </summary>
        private void RefreshUI()
        {
            // Update user list
            UserListBox.ItemsSource = Users;

            // Update status
            StatusText.Text = $"Loaded {Users.Count} users";
        }

        /// <summary>
        /// Handle user selection change
        /// </summary>
        private void OnUserChanged(User user)
        {
            if (user == null) return;

            // Update UI with user details
            UserDetailsPanel.DataContext = user;

            // Log activity
            LogActivity($"Selected user: {user.FullName}");
        }

        /// <summary>
        /// Handle errors
        /// </summary>
        private void HandleError(Exception ex, string message)
        {
            // Log error
            LogActivity($"ERROR: {message} - {ex.Message}");

            // Show error message to user
            MessageBox.Show(
                $"{message}: {ex.Message}",
                "Error",
                MessageBoxButton.OK,
                MessageBoxImage.Error);
        }

        /// <summary>
        /// Log activity
        /// </summary>
        private void LogActivity(string message)
        {
            // In a real app, this would log to a file or service
            Console.WriteLine($"[{DateTime.Now:yyyy-MM-dd HH:mm:ss}] {message}");

            // Update status bar
            StatusText.Text = message;
        }

        /// <summary>
        /// Event handler for Save button click
        /// </summary>
        private async void SaveButton_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                // Save current user
                if (CurrentUser != null)
                {
                    await _userService.SaveUserAsync(CurrentUser);
                    _isDirty = false;

                    // Log activity
                    LogActivity($"Saved user: {CurrentUser.FullName}");
                }
            }
            catch (Exception ex)
            {
                HandleError(ex, "Error saving user");
            }
        }

        /// <summary>
        /// Event handler for Refresh button click
        /// </summary>
        private async void RefreshButton_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                // Check for unsaved changes
                if (_isDirty)
                {
                    var result = MessageBox.Show(
                        "You have unsaved changes. Do you want to continue?",
                        "Unsaved Changes",
                        MessageBoxButton.YesNo,
                        MessageBoxImage.Warning);

                    if (result == MessageBoxResult.No)
                    {
                        return;
                    }
                }

                // Reload users
                Users = await _userService.GetUsersAsync();
                RefreshUI();

                // Log activity
                LogActivity("Refreshed user data");
            }
            catch (Exception ex)
            {
                HandleError(ex, "Error refreshing data");
            }
        }

        /// <summary>
        /// Event handler for Settings button click
        /// </summary>
        private void SettingsButton_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                // Open settings dialog
                var settingsDialog = new SettingsDialog(_settingsManager.LoadSettings());
                var result = settingsDialog.ShowDialog();

                if (result == true)
                {
                    // Save new settings
                    var newSettings = settingsDialog.Settings;
                    _settingsManager.SaveSettings(newSettings);

                    // Apply new settings
                    ApplySettings(newSettings);

                    // Log activity
                    LogActivity("Settings updated");
                }
            }
            catch (Exception ex)
            {
                HandleError(ex, "Error opening settings");
            }
        }

        /// <summary>
        /// Event handler for window closing
        /// </summary>
        private void Window_Closing(object sender, System.ComponentModel.CancelEventArgs e)
        {
            // Check for unsaved changes
            if (_isDirty)
            {
                var result = MessageBox.Show(
                    "You have unsaved changes. Do you want to exit?",
                    "Unsaved Changes",
                    MessageBoxButton.YesNo,
                    MessageBoxImage.Warning);

                if (result == MessageBoxResult.No)
                {
                    e.Cancel = true;
                    return;
                }
            }

            // Save window position and size
            var settings = _settingsManager.LoadSettings();
            settings.WindowWidth = Width;
            settings.WindowHeight = Height;
            _settingsManager.SaveSettings(settings);

            // Log activity
            LogActivity("Application closing");
        }
    }
}