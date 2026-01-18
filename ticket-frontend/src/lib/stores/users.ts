import { writable, type Writable } from "svelte/store";

export interface User {
  id: string;
  name: string;
}

// Static list of users
export const users: User[] = [
  { id: "user-0", name: "Admin User" },
  { id: "user-1", name: "IT Person" },
  { id: "user-2", name: "Frontend Developer" },
  { id: "user-3", name: "Backend Developer" },
  { id: "user-4", name: "Database Developer" },
  { id: "user-5", name: "UI Designer" },
  { id: "user-6", name: "AI Engineer" },
  { id: "user-7", name: "Network Engineer" },
];

// Local storage key for persisting user
const USER_STORAGE_KEY = "narr0w_current_user_id";

// Current user store
export const currentUser: Writable<User | null> = writable(null);

// Helper to get user initials
export function getUserInitials(name: string): string {
  const parts = name.trim().split(/\s+/);
  if (parts.length === 1) {
    return parts[0].substring(0, 2).toUpperCase();
  }
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

// Set current user and persist to localStorage
export function setCurrentUser(user: User) {
  currentUser.set(user);
  if (typeof localStorage !== "undefined") {
    localStorage.setItem(USER_STORAGE_KEY, user.id);
  }
}

// Get user by ID
export function getUserById(id: string): User | undefined {
  return users.find(user => user.id === id);
}

// Initialize user from localStorage or default to users[1]
function initializeUser() {
  if (typeof localStorage !== "undefined") {
    const savedUserId = localStorage.getItem(USER_STORAGE_KEY);
    if (savedUserId) {
      const savedUser = getUserById(savedUserId);
      if (savedUser) {
        currentUser.set(savedUser);
        return;
      }
    }
  }
  // Default to users[1] if nothing saved or not found
  currentUser.set(users[1]);
}

// Initialize on module load
initializeUser();
