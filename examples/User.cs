using System;
using System.ComponentModel;
using System.Runtime.CompilerServices;

namespace SampleApplication
{
    /// <summary>
    /// Represents a user in the system
    /// </summary>
    public class User : INotifyPropertyChanged
    {
        private int _id;
        private string _firstName;
        private string _lastName;
        private string _email;
        private string _phone;
        private bool _isActive;

        /// <summary>
        /// Unique identifier for the user
        /// </summary>
        public int Id
        {
            get => _id;
            set
            {
                if (_id != value)
                {
                    _id = value;
                    OnPropertyChanged();
                }
            }
        }

        /// <summary>
        /// User's first name
        /// </summary>
        public string FirstName
        {
            get => _firstName;
            set
            {
                if (_firstName != value)
                {
                    _firstName = value;
                    OnPropertyChanged();
                    OnPropertyChanged(nameof(FullName));
                }
            }
        }

        /// <summary>
        /// User's last name
        /// </summary>
        public string LastName
        {
            get => _lastName;
            set
            {
                if (_lastName != value)
                {
                    _lastName = value;
                    OnPropertyChanged();
                    OnPropertyChanged(nameof(FullName));
                }
            }
        }

        /// <summary>
        /// User's email address
        /// </summary>
        public string Email
        {
            get => _email;
            set
            {
                if (_email != value)
                {
                    _email = value;
                    OnPropertyChanged();
                }
            }
        }

        /// <summary>
        /// User's phone number
        /// </summary>
        public string Phone
        {
            get => _phone;
            set
            {
                if (_phone != value)
                {
                    _phone = value;
                    OnPropertyChanged();
                }
            }
        }

        /// <summary>
        /// Whether the user is active in the system
        /// </summary>
        public bool IsActive
        {
            get => _isActive;
            set
            {
                if (_isActive != value)
                {
                    _isActive = value;
                    OnPropertyChanged();
                }
            }
        }

        /// <summary>
        /// User's full name (derived from first and last name)
        /// </summary>
        public string FullName => $"{FirstName} {LastName}";

        /// <summary>
        /// Constructor
        /// </summary>
        public User()
        {
            _isActive = true;
        }

        /// <summary>
        /// Create a new user with specified details
        /// </summary>
        public User(int id, string firstName, string lastName, string email, string phone, bool isActive = true)
        {
            _id = id;
            _firstName = firstName;
            _lastName = lastName;
            _email = email;
            _phone = phone;
            _isActive = isActive;
        }

        /// <summary>
        /// Property changed event
        /// </summary>
        public event PropertyChangedEventHandler PropertyChanged;

        /// <summary>
        /// Raise the PropertyChanged event
        /// </summary>
        protected virtual void OnPropertyChanged([CallerMemberName] string propertyName = null)
        {
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
        }

        /// <summary>
        /// Returns a string representation of the user
        /// </summary>
        public override string ToString()
        {
            return FullName;
        }
    }
}