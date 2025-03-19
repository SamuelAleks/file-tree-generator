using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace SampleApplication
{
    /// <summary>
    /// Service for managing users
    /// </summary>
    public class UserService
    {
        // In-memory user database for demo purposes
        private readonly List<User> _users;

        /// <summary>
        /// Constructor
        /// </summary>
        public UserService()
        {
            // Initialize with sample data
            _users = new List<User>
            {
                new User(1, "John", "Doe", "john.doe@example.com", "555-1234", true),
                new User(2, "Jane", "Smith", "jane.smith@example.com", "555-5678", true),
                new User(3, "Bob", "Johnson", "bob.johnson@example.com", "555-9012", false),
                new User(4, "Alice", "Williams", "alice.williams@example.com", "555-3456", true),
                new User(5, "Mike", "Brown", "mike.brown@example.com", "555-7890", true)
            };
        }

        /// <summary>
        /// Get all users asynchronously
        /// </summary>
        public async Task<List<User>> GetUsersAsync()
        {
            // Simulate async database operation
            await Task.Delay(500);

            // Return a copy of the users list
            return _users.Select(u => new User(
                u.Id,
                u.FirstName,
                u.LastName,
                u.Email,
                u.Phone,
                u.IsActive)
            ).ToList();
        }

        /// <summary>
        /// Get a user by ID asynchronously
        /// </summary>
        public async Task<User> GetUserByIdAsync(int id)
        {
            // Simulate async database operation
            await Task.Delay(200);

            // Find user with matching ID
            var user = _users.FirstOrDefault(u => u.Id == id);

            // Return null if user not found
            if (user == null)
            {
                return null;
            }

            // Return a copy of the user
            return new User(
                user.Id,
                user.FirstName,
                user.LastName,
                user.Email,
                user.Phone,
                user.IsActive
            );
        }

        /// <summary>
        /// Save a user asynchronously
        /// </summary>
        public async Task SaveUserAsync(User user)
        {
            if (user == null)
            {
                throw new ArgumentNullException(nameof(user));
            }

            // Simulate async database operation
            await Task.Delay(300);

            // Find existing user
            var existingUser = _users.FirstOrDefault(u => u.Id == user.Id);

            if (existingUser != null)
            {
                // Update existing user
                existingUser.FirstName = user.FirstName;
                existingUser.LastName = user.LastName;
                existingUser.Email = user.Email;
                existingUser.Phone = user.Phone;
                existingUser.IsActive = user.IsActive;
            }
            else
            {
                // Add new user with generated ID
                var newId = _users.Count > 0 ? _users.Max(u => u.Id) + 1 : 1;
                user.Id = newId;
                _users.Add(user);
            }
        }

        /// <summary>
        /// Delete a user asynchronously
        /// </summary>
        public async Task DeleteUserAsync(int id)
        {
            // Simulate async database operation
            await Task.Delay(200);

            // Find user with matching ID
            var user = _users.FirstOrDefault(u => u.Id == id);

            // Remove user if found
            if (user != null)
            {
                _users.Remove(user);
            }
        }
    }
}